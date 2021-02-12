import argparse

from omc_kube.kube.kube_resource import KubeResource


class Pod(KubeResource):
    pass

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
