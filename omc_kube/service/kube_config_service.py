import os
import shutil

from omc.common import CmdTaskMixin
from omc.utils import file_utils


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

        # download ssl files
        print("downloading ssl certificate to %s" % the_kube_config_dir)
        certificate_download_cmd = 'scp -r %s:/opt/kubernetes/ssl/ %s' % (k8s_resource, the_kube_config_dir)
        self.run_cmd(certificate_download_cmd)

        kube_config_file = os.path.join(the_kube_config_dir, 'config')
        file_utils.inplace_replace(kube_config_file, '/opt/kubernetes/ssl', os.path.join(the_kube_config_dir, 'ssl'))