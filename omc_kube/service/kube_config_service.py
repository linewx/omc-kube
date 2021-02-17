import os
import shutil

from omc.common import CmdTaskMixin
from omc.utils import file_utils
from omc.utils.object_utils import ObjectUtils


class KubeConfigService(CmdTaskMixin):
    def sync(self, k8s_resource, kube_config_dir):

        the_kube_config_dir = os.path.join(kube_config_dir, k8s_resource)

        if os.path.exists(the_kube_config_dir):
            shutil.rmtree(the_kube_config_dir)

        file_utils.make_directory(the_kube_config_dir)

        # download config file
        print("downloading config file to %s" % the_kube_config_dir)

        config_download_cmd = 'scp %s:/root/.kube/config %s' % (k8s_resource, the_kube_config_dir)
        self.run_cmd(config_download_cmd)

        ssl_dir = self._get_cert_dir(os.path.join(the_kube_config_dir, 'config'))

        # download ssl files
        print("downloading ssl certificate to %s" % the_kube_config_dir)
        certificate_download_cmd = 'scp -r %s:%s %s' % (k8s_resource,ssl_dir, the_kube_config_dir)
        self.run_cmd(certificate_download_cmd)

        kube_config_file = os.path.join(the_kube_config_dir, 'config')
        file_utils.inplace_replace(kube_config_file, ssl_dir, os.path.join(the_kube_config_dir, 'ssl'))

    def _get_cert_dir(self, config_file):
        import yaml
        with open(config_file) as f:
            result = yaml.load(f, yaml.FullLoader)
            path = (ObjectUtils.get_node(result, 'clusters[0].cluster.certificate-authority'))
            return os.path.dirname(path)

if __name__ == '__main__':
    import yaml
    with open('/Users/luganlin/.omc/config/kube/cd219/config') as f:
        result = yaml.load(f, yaml.FullLoader)
        path = (ObjectUtils.get_node(result, 'clusters[0].cluster.certificate-authority'))
        print(os.path.dirname(path))
        print(result)