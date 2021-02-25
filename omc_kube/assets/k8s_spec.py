import json


# todo@rain
# 1. pre-calculate resource spec for strategy patch merge
# 2. calcuate for resource completion
from omc.core import console


class K8sSpec:
    def __init__(self, spec_file):
        with open(spec_file) as f:
            self.content = json.load(f)
            self.definitions = self.content['definitions']

    def _get_one_definition(self, resourceType):
        return self.definitions.get(resourceType)

    def _get_one_definition_properties(self, resourceType):
        return self._get_one_definition(resourceType).get('properties')

    def _get_one_definition_type(self, resourceType):
        return self._get_one_definition(resourceType).get('type')

    def gen_definition_tree(self, root_node):
        properties = self._get_one_definition_properties(root_node)
        results = {}
        if properties:
            for one_property_name, one_property_value in properties.items():
                if '$ref' in one_property_value:
                    results[one_property_name] = \
                        {**self.gen_definition_tree(one_property_value['$ref'].replace('#/definitions/', '')),
                         '_definition': one_property_value
                         }
                elif one_property_value.get('type') == 'array':
                    items = one_property_value['items']
                    if '$ref' in items:
                        results[one_property_name] = {
                            **self.gen_definition_tree(items['$ref'].replace('#/definitions/', '')),
                            '_definition': one_property_value
                        }
                    else:
                        results[one_property_name] = {
                            '_definition': one_property_value
                        }
                else:
                    results[one_property_name] = {
                        '_definition': one_property_value
                    }
        else:
            return {
                '_definition': self._get_one_definition(root_node)
            }
        return results

    def gen_sample(self, root_node):
        properties = self._get_one_definition_properties(root_node)
        results = {}
        if properties:
            for one_property_name, one_property_value in properties.items():
                if '$ref' in one_property_value:
                    results[one_property_name] = self.gen_sample(
                        one_property_value['$ref'].replace('#/definitions/', ''))
                elif one_property_value.get('type') == 'array':
                    items = one_property_value['items']
                    if '$ref' in items:
                        results[one_property_name] = [self.gen_sample(items['$ref'].replace('#/definitions/', ''))]

                    else:
                        results[one_property_name] = ['']
                else:
                    results[one_property_name] = ''
        else:
            return ''
        return results


def pprint(obj):
    console.log(json.dumps(obj, indent=2))


if __name__ == '__main__':
    spec = K8sSpec('/Users/luganlin/git/omc-all/omc-kube/omc_kube/assets/swagger.json')

    # pprint(spec._get_one_definition_properties("io.k8s.api.apps.v1.Deployment"))
    # pprint(spec.gen_definition_tree("io.k8s.api.apps.v1.Deployment"))

    resources = [('pod', 'io.k8s.api.core.v1.Pod'),
                 ('pv', 'io.k8s.api.core.v1.PersistentVolume'),
                 ('endpoints', 'io.k8s.api.core.v1.Endpoints'),
                 ('ingress', 'io.k8s.api.networking.v1.Ingress'),
                 ('deployment', 'io.k8s.api.apps.v1.Deployment'),
                 ('pvc', 'io.k8s.api.core.v1.PersistentVolumeClaim'),
                 ('configmap', 'io.k8s.api.core.v1.ConfigMap'),
                 ('service', 'io.k8s.api.core.v1.Service'),
                 ('event', 'io.k8s.api.events.v1.Event')]
    # '/Users/luganlin/git/omc-all/omc-kube/omc_kube/kube/deployment/_deployment_completion.json'
    for resource,name in resources:
        with open('/Users/luganlin/git/omc-all/omc-kube/omc_kube/assets/_%s_completion.json' % (resource),
                  'w') as f:
            json.dump(spec.gen_sample(name), f, indent=2)
    # pprint(spec._get_one_definition_type("io.k8s.api.apps.v1.Deployment"))
