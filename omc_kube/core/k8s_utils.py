import json
import re

from kubernetes import client, config
from omc.common import CmdTaskMixin
from functools import wraps

from omc.utils.object_utils import ObjectUtils


class KubernetesClient(CmdTaskMixin):
    def __init__(self, config_file=None):
        if not config_file:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file)

        self.config_file = config_file

        corev1api = client.CoreV1Api()
        appsv1api = client.AppsV1Api()
        extensionsv1beta1api = client.ExtensionsV1beta1Api()
        self.client_instances = [corev1api, appsv1api, extensionsv1beta1api]

    def __getattr__(self, item: str):
        for one_instance in self.client_instances:
            if hasattr(one_instance, item):
                f = getattr(one_instance, item)

                @wraps(f)
                def wrapper(*args, **kwds):
                    if kwds is not None and '_preload_content' in kwds:
                        return f(*args, **kwds)
                    else:
                        result = f(*args, **kwds, _preload_content=False)
                        the_result = json.loads(result.data.decode('UTF-8'))
                        return the_result

                return wrapper

    def get_namespace(self, resource_type: str, resource_name: str):
        list_namespaces = getattr(self, "list_%s_for_all_namespaces" % resource_type)
        all_namespaces = list_namespaces()
        for one in all_namespaces.get('items'):
            if ObjectUtils.get_node(one, 'metadata.name') == resource_name:
                return ObjectUtils.get_node(one, 'metadata.namespace')

    ##################################
    ###### kubectl impl ##############
    ##################################

    def apply(self, file):
        # todo: since apply not supported, need to impl

        # option1: using kubectl instead
        # option2: upgrade k8s version to support server-side apply
        # option3: implemented in client side myself
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''

        cmd = "kubectl %(config)s apply -f %(file)s" % locals()
        result = self.run_cmd(cmd)

    def edit(self, resource_type: str, resource_name: str, namespace: str):
        resource_type = self.reconcile_resource_type(resource_type)
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        self.run_cmd("kubectl %(config)s edit %(resource_type)s %(resource_name)s --namespace %(namespace)s" % locals())

    def portforward(self):
        pass

    def download(self, resource_name, namespace, local_dir, remote_dir, container=None):
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        container_options = '' if not container else '-c ' + container
        cmd = "kubectl %(config)s cp %(container_options)s %(namespace)s/%(resource_name)s:%(remote_dir)s %(local_dir)s" % locals()
        self.run_cmd(cmd)

    def upload(self, resource_name, namespace, local_dir, remote_dir, container=None):

        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        container_options = '' if not container else '-c ' + container
        cmd = "kubectl %(config)s cp %(container_options)s %(local_dir)s %(namespace)s/%(resource_name)s:%(remote_dir)s" % locals()
        self.run_cmd(cmd)

    def exec(self, resource_type, resource_name, namespace, command, container=None, stdin=True):
        resource_type = self.reconcile_resource_type(resource_type)
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        interactive_option = '-it' if stdin else ''
        container_options = '' if not container else '-c ' + container
        cmd = 'kubectl %(config)s exec %(interactive_option)s %(resource_type)s/%(resource_name)s %(container_options)s --namespace %(namespace)s -- %(command)s' % locals()
        self.run_cmd(cmd)

    def get(self, resource_type, resource_name='', namespace='all', output='yaml'):
        resource_type = self.reconcile_resource_type(resource_type)
        resource_name = '' if not resource_name else resource_name
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        namespace_options = ''
        if namespace == 'all':
            namespace_options = '-A'
        else:
            namespace_options = '--namespace %s' % namespace

        output_options = '' if not output else '-o ' + output

        cmd = 'kubectl %(config)s get %(resource_type)s %(resource_name)s %(namespace_options)s -o wide' % locals()
        result = self.run_cmd(cmd, capture_output=True, verbose=False)
        return result.stdout.decode('UTF-8')

    def describe(self, resource_type, resource_name=None, namespace='all'):
        resource_type = self.reconcile_resource_type(resource_type)
        config = ' --kubeconfig %s ' % self.config_file if self.config_file else ''
        namespace_options = ''
        if namespace == 'all':
            namespace_options = '-A'
        else:
            namespace_options = '--namespace %s' % namespace

        resource_name = '' if not resource_name else resource_name
        cmd = 'kubectl %(config)s describe %(resource_type)s %(resource_name)s %(namespace_options)s' % locals()
        result = self.run_cmd(cmd, capture_output=True, verbose=False)
        return result.stdout.decode("UTF-8")

    def reconcile_resource_type(self, resource_type):
        resource_type_mapping = {
            'config_map': 'configmap'
        }

        if resource_type in resource_type_mapping:
            return resource_type_mapping[resource_type]
        else:
            return resource_type


# https://github.com/kubernetes/community/blob/master/contributors/devel/sig-api-machinery/strategic-merge-patch.md
# openapi spec https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json
#

'''
{
    "spec": {
        "template": {
            "spec": {
                "$setElementOrder/containers": [
                    {
                        "name": "idm"
                    }
                ],
                "containers": [
                    {
                        "$setElementOrder/env": [
                            {
                                "name": "EXTERNAL_NAME"
                            },
                            {
                                "name": "EXTERNAL_NAME1"
                            },
                            {
                                "name": "IDM_MOUNT_ROOT"
                            },
                            {
                                "name": "JVM_MAX_SIZE"
                            },
                            {
                                "name": "CATALINA_OPTS"
                            },
                            {
                                "name": "HPSSO_INIT_STRING"
                            },
                            {
                                "name": "SAML2_ENABLE"
                            },
                            {
                                "name": "SAML_KEYSTORE_PASSWORD_KEY"
                            },
                            {
                                "name": "saml_keystore_password_key"
                            }
                        ],
                        "env": [
                            {
                                "name": "EXTERNAL_NAME1",
                                "value": "idm-svc1"
                            }
                        ],
                        "name": "idm"
                    }
                ]
            }
        }
    }
}
'''


class StrategicMergePatch:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.api_spec = {
            'spec.template.spec.containers': {
                "type": "array",
                "x-kubernetes-patch-merge-key": "name",
                "x-kubernetes-patch-strategy": "merge"
            },
            'spec.template.spec.containers.env': {
                "type": "array",
                "x-kubernetes-patch-merge-key": "name",
                "x-kubernetes-patch-strategy": "merge"
            },

        }

    def flatten_key(self, key):
        return re.sub("\[\d+\]", '', key)

    def parse_one_key(self, key):
        is_array = False
        index = -1
        key = key
        if '[' in key and ']' in key:
            is_array = True
            parsed_key, parsed_index = re.findall('(\w+)\[(\d*)\]', key)[0]
            key = parsed_key

            if parsed_index:
                index = int(parsed_index)
            else:
                index = -1

        return key, is_array, index
        # return {
        #     'key': key,
        #     'is_array': is_array,
        #     'index': index
        # }

    def gen_strategic_merge_patch(self, origin, key_array, value, action, path):
        '''
        'spec.template.spec.containers[0].env[1]',
         {'name': 'name1', 'value': 'value1'}
        '''
        keys = key_array.copy()
        one_key = keys.pop(0)
        current_path = path.copy()  # raw path, with array index
        current_path.append(one_key)

        the_key, is_array, index = self.parse_one_key(one_key)
        current_key_path = '.'.join(
            [*path, the_key])  # with old array index, without current index, for get object value
        current_flatten_path = self.flatten_key('.'.join([*path, the_key]))  # no array index, only for api spec usage

        if not is_array:
            if not keys:
                # no key any more
                if action == 'set':
                    return {the_key: value}
                elif action == 'delete':
                    return {the_key: None}
            else:
                return {the_key: self.gen_strategic_merge_patch(origin, keys, value, action, current_path)}
        else:

            the_value = value

            if current_flatten_path in self.api_spec:
                # for array, we have stratgic merge rule
                current_value = ObjectUtils
                ObjectUtils.get_node(origin, current_key_path)

                merge_key = self.api_spec[current_flatten_path]['x-kubernetes-patch-merge-key']
                patch_strategy = self.api_spec[current_flatten_path]['x-kubernetes-patch-strategy']
                results = {}

                '''
                 "$setElementOrder/containers": [
                    {
                        "name": "idm"
                    }
                ],
                '''
                if keys:
                    # has children
                    results['$setElementOrder/%s' % the_key] = [{merge_key: one.get(merge_key)} for one in
                                                                current_value]
                    results[the_key] = [
                        {
                            merge_key: current_value[index].get(merge_key),
                            **self.gen_strategic_merge_patch(origin, keys, the_value, action, current_path)
                        }
                    ]

                if not keys:
                    results['$setElementOrder/%s' % the_key] = [{merge_key: one.get(merge_key)} for one in
                                                                current_value]
                    if action == 'set':
                        one_item = []
                        if isinstance(value, dict):
                            value = {**value, merge_key: current_value[index].get(merge_key)}
                        one_item.insert(index, value)
                        results[the_key] = one_item
                    elif action == 'delete':
                        one_item = []
                        # one_item.insert(index, value)
                        one_item.append({"$patch": 'delete', **value})
                        results[the_key] = one_item
                return results

            else:
                # if no merge rule, merge normally
                current_value = ObjectUtils.get_node(origin, current_key_path)
                current_value = current_value if current_value else []
                current_value.insert(index, the_value)


if __name__ == '__main__':
    # client = KubernetesClient("~/.omc/config/kube/nightly1/config")
    # the_namespace = client.get_namespace("service", "smarta-smart-ticket-svc")
    # print(the_namespace)
    #
    # print(client.list_config_map_for_all_namespaces(watch=False))
    # print(client.list_pod_for_all_namespaces(watch=False))
    # print(client.list_deployment_for_all_namespaces(watch=False))
    # print(client.list_service_for_all_namespaces(watch=False))
    # print(client.list_endpoints_for_all_namespaces(watch=False))
    smp = StrategicMergePatch()
    origin = None
    with open('/Users/luganlin/git/mf/omc/omc/assets/k8s/deployment_sample.json') as f:
        origin = json.load(f)
    # result = smp.gen_strategic_merge_patch(origin, 'spec.template.spec.containers[0].env[]'.split('.'),
    #                                        {'name': 'name1', 'value': 'value1'}, 'delete', [])

    # # print(json.dumps(result, indent=2))
    #
    result1 = smp.gen_strategic_merge_patch(origin, 'spec.template.spec.containers[0].livenessProbe'.split('.'),
                                            'value1', 'delete', [])

    print(json.dumps(result1, indent=2))
    value = json.loads('{"command": ["/bin/sh"], "args": ["-c", "while true; do echo hello; sleep 10;done"]}')
    result2 = smp.gen_strategic_merge_patch(origin, 'spec.template.spec.containers[0]'.split('.'),
                                            value, 'set', [])

    print(json.dumps(result2, indent=2))
    # print(smp.gen_strategic_merge_patch(origin, 'spec.template.spec.containers[0].env',{'name': 'name1', 'value': 'value1'}))

    # print(json.loads('{"command": ["/bin/sh"], "args": ["-c", "while true; do echo hello; sleep 10;done"]}'))
