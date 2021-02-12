from omc_kube.kube.kube_resource import KubeResource


class Configmap(KubeResource):
    def _get_kube_api_resource_type(self):
        return 'config_map'
