from omc.common import CmdTaskMixin
from omc_kube.kube.kube_node_resource import KubeNodeResource


class Node(KubeNodeResource, CmdTaskMixin):
    pass
