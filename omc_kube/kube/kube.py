import os

from omc.common import CmdTaskMixin
from omc.config import settings
from omc.core.decorator import filecache
from omc.core.resource import Resource

from omc_kube.core import KubernetesClient


class Kube(Resource, CmdTaskMixin):
    def _description(self):
        return 'The Kubernetes command-line tool'

    @filecache(duration=-1, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(False))
        if not self._have_resource_value():
            if os.path.exists(settings.OMC_KUBE_CONFIG_DIR):
                resources = os.listdir(settings.OMC_KUBE_CONFIG_DIR)
                results.append("\n".join(self._get_completion(resources, True)))

        return "\n".join(results)

    def _before_sub_resource(self):
        try:
            if self._have_resource_value():
                resource_value = self._get_one_resource_value()
                client = KubernetesClient(os.path.join(settings.OMC_KUBE_CONFIG_DIR, resource_value, 'config'))
            else:
                client = KubernetesClient()

            self.context['common'] = {
                'client': client
            }
        except:
            # some action no need to create load config, get config action e.g.
            pass


if __name__ == '__main__':
    client = KubernetesClient()
    ret = client.list_service_for_all_namespaces(watch=False)

    # print(client.read_namespaced_pod("postgres-svc-5685d4bc7-l6j4m", 'default'))
    # print(client.read_namespaced_pod_template("postgres-svc-5685d4bc7-l6j4m", 'default'))
    # print(client.read_namspaced_event("postgres-svc-5685d4bc7-l6j4m", 'default'))
    print(ret)
    # for i in ret.items:
    #     print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
