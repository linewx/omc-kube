from omc.common import CmdTaskMixin
from omc.resources.kube.kube_section_resource import KubeNodeResource


class Node(KubeNodeResource, CmdTaskMixin):
    pass
