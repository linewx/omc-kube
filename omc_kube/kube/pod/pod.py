import argparse

from omc.common.common_completion import CompletionContent
from omc.common.formatter import Formatter
from omc.config import settings
from omc.utils.object_utils import ObjectUtils

from omc_kube.kube.kube_resource import KubeResource


class Pod(KubeResource):
    'smallest deployable units of computing that you can create and manage in Kubernetes.'

    def download(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--local', help='local dir')
        parser.add_argument('--remote', help='remote dir')
        args = parser.parse_args(self._get_action_params())

        resource_name = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)
        self.client.download(resource_name, namespace, args.local, args.remote)

    def upload(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--local', help='local dir')
        parser.add_argument('--remote', help='remote dir')
        args = parser.parse_args(self._get_action_params())

        resource_name = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)
        self.client.upload(resource_name, namespace, args.local, args.remote)

    # def _resource_completion(self, short_mode=True):
    #     ret = self._list_resource_for_all_namespaces(timeout_seconds=settings.COMPETION_TIMEOUT)
    #     results = Formatter.format_completions(
    #         [(ObjectUtils.get_node(one, 'metadata.name'),
    #           ObjectUtils.get_node(one, 'metadata.namespace'),
    #           ObjectUtils.get_node(one, 'status.phase'),
    #           ObjectUtils.get_node(one, 'status.podIP'),
    #           ObjectUtils.get_node(one, 'spec.nodeName'),
    #           )
    #          for one in ret.get('items')])
    #
    #     return CompletionContent(results)
