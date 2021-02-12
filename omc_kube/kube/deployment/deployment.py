import json

from omc_kube.core import StrategicMergePatch
from omc_kube.kube.kube_resource import KubeResource


class Deployment(KubeResource):
    def pause(self):
        resource_content = self._get_resource()
        namespace = self._get_namespace()
        config_key = 'spec.template.spec.containers[0]'
        config_value = json.loads('{"command": ["/bin/sh"], "args": ["-c", "while true; do echo hello; sleep 10;done"]}')
        patch_func = getattr(self.client, 'patch_namespaced_' + self._get_kube_api_resource_type())
        # patch_object = utils.build_object(config_key, config_value)
        patch_object = StrategicMergePatch.get_instance().gen_strategic_merge_patch(resource_content, config_key.split('.'),
                                                                                    config_value, 'set', [])
        new_result = patch_func(self._get_one_resource_value(), namespace, patch_object)
        print(new_result)