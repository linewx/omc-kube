from omc_kube.kube.kube_resource import KubeResource


class Configmap(KubeResource):
    """
    used to store non-confidential data in key-value pairs
    """
    def _get_kube_api_resource_type(self):
        return 'config_map'
