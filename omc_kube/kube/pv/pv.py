from omc.common.common_completion import CompletionContent
from omc.common.formatter import Formatter

from omc_kube.kube.kube_resource import KubeResource


class Pv(KubeResource):
    '''kubenetes persistent volumns'''
    pass

    def _resource_completion(self, short_mode=True):
        output = self.client.get(self._get_kube_api_resource_type())

        results = []

        for one in output.splitlines()[1:]:
            one_line = one.strip().split()
            # no namespace, no need swap position
            # one_line[0],one_line[1] = one_line[1],one_line[0]
            results.append(one_line)

        # ret = self._list_resource_for_all_namespaces(timeout_seconds=settings.COMPETION_TIMEOUT)
        # results.extend(
        #     self._get_completion([ObjectUtils.get_node(one, 'metadata.name') for one in ret.get('items')], True))

        return CompletionContent(Formatter.format_completions(results))