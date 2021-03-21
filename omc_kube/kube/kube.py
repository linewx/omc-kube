import logging
import os

from omc.common import CmdTaskMixin
from omc.common.common_completion import CompletionContent
from omc.common.formatter import Formatter
from omc.config import settings
from omc.core import console
from omc.core.decorator import filecache
from omc.core.resource import Resource
from omc.utils.object_utils import ObjectUtils
from ruamel_yaml import YAML

from omc_kube.core import KubernetesClient

logger = logging.getLogger(__name__)


class Kube(Resource, CmdTaskMixin):
    def _description(self):
        return 'The Kubernetes command-line tool'

    def _resource_completion(self, short_mode=True):
        results = []
        headers = ('NAME', 'SERVER', 'CLUSTER', 'CONTEXT')
        yaml = YAML()
        results.append(headers)
        if os.path.exists(settings.OMC_KUBE_CONFIG_DIR):
            resources = os.listdir(settings.OMC_KUBE_CONFIG_DIR)
            for one_resource in resources:
                try:
                    with open(os.path.join(settings.OMC_KUBE_CONFIG_DIR, one_resource, 'config')) as f:
                        content = yaml.load(f)
                        one_item = (
                            one_resource,
                            ObjectUtils.get_node(content, "clusters[0].cluster.server"),
                            ObjectUtils.get_node(content, "clusters[0].name"),
                            ObjectUtils.get_node(content, "current-context")
                        )
                        results.append(one_item)
                except Exception as e:
                    logger.error(e, exc_info=True)

        return CompletionContent(Formatter.format_completions(results))

    def _before_sub_resource(self):
        try:
            if self._have_resource_value():
                resource_value = self._get_one_resource_value()
                client = KubernetesClient(os.path.join(settings.OMC_KUBE_CONFIG_DIR, resource_value, 'config'))
            else:
                client = KubernetesClient()

            self.context['common'] = {'client': client}
        except Exception as e:
            # some action no need to create load config, get config action e.g.
            raise Exception('invalid kubenetes config')


if __name__ == '__main__':
    client = KubernetesClient()
    ret = client.list_service_for_all_namespaces(watch=False)
    yaml = YAML()
    with open('/Users/luganlin/.omc/config/kube/cd150/config') as f:
        content = yaml.load(f)
        print(ObjectUtils.get_node(content, "clusters[0].cluster.server"))

    # print(client.read_namespaced_pod("postgres-svc-5685d4bc7-l6j4m", 'default'))
    # print(client.read_namespaced_pod_template("postgres-svc-5685d4bc7-l6j4m", 'default'))
    # print(client.read_namspaced_event("postgres-svc-5685d4bc7-l6j4m", 'default'))
    console.log(ret)
    # for i in ret.items:
    #     print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
