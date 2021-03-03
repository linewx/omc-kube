import json

from omc.common.common_completion import CompletionContent
from omc.common.formatter import Formatter
from omc.config import settings
from omc.core import console
from omc.utils.object_utils import ObjectUtils

from omc_kube import utils
from omc_kube.core import StrategicMergePatch
from omc_kube.kube.kube_resource import KubeResource
from omc_kube.utils import time_util


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
        console.log(new_result)

    def _get_ready_status(self, one):
        replicas = 0 if ObjectUtils.get_node(one, 'status.replicas') is None else  ObjectUtils.get_node(one, 'status.replicas')
        unavailable_replicas = 0 if ObjectUtils.get_node(one, 'status.unavailableReplicas') is None else ObjectUtils.get_node(one, 'status.unavailableReplicas')
        updated_replicas = 0 if ObjectUtils.get_node(one, 'status.updatedReplicas') is None else ObjectUtils.get_node(one, 'status.updatedReplicas')
        available_replicas = replicas - unavailable_replicas
        return str(available_replicas) + '/' + str(replicas)


    def _resource_completion(self, short_mode=True):
        ret = self._list_resource_for_all_namespaces(timeout_seconds=settings.COMPETION_TIMEOUT)
        results = Formatter.format_completions(
            [(ObjectUtils.get_node(one, 'metadata.name'),
              ObjectUtils.get_node(one, 'metadata.namespace'),
              self._get_ready_status(one),
              time_util.calculate_age(time_util.fromisotime(ObjectUtils.get_node(one, 'metadata.creationTimestamp'))),
              )
             for one in ret.get('items')])

        return CompletionContent(results)