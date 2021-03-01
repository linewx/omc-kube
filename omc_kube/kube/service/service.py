from omc.common.common_completion import CompletionContent
from omc.common.formatter import Formatter
from omc.config import settings
from omc.utils.object_utils import ObjectUtils

from omc_kube.kube.kube_resource import KubeResource


class Service(KubeResource):
    def _build_ports(self, ports):
        if not ports:
            return ''
        items = [self._build_one_port(port) for port in ports]
        return ','.join(items)

    def _build_one_port(self, one):
        result = ''
        if 'port' in one:
            result  = str(one.get('port'))
        if 'nodePort' in one:
            result = result + ":" + str(one.get('nodePort'))
        if 'protocol' in one:
            result = result + "/" + str(one.get('protocol'))
        return result

    def _build_selector(self, selectors):
        if selectors:
            return ','.join([str(k) + '=' + str(v) for k,v in selectors.items()])
        else:
            return ''

    def _resource_completion(self, short_mode=True):
        ret = self._list_resource_for_all_namespaces(timeout_seconds=settings.COMPETION_TIMEOUT)
        results = Formatter.format_completions(
            [(ObjectUtils.get_node(one, 'metadata.name'),
              ObjectUtils.get_node(one, 'metadata.namespace'),
              ObjectUtils.get_node(one, 'spec.type'),
              ObjectUtils.get_node(one, 'spec.clusterIP'),
              self._build_ports(ObjectUtils.get_node(one, 'spec.ports')),
              self._build_selector(ObjectUtils.get_node(one, 'spec.selector')),
              )
             for one in ret.get('items')])

        return CompletionContent(results)