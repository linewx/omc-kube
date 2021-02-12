import argparse

from omc.core.decorator import filecache

from omc.common import CmdTaskMixin

from omc.core import Resource


class Container(Resource, CmdTaskMixin):
    def __init__(self, context={}, type='web'):
        super().__init__(context, type)
        self.client = self.context['common']['client']

    def _get_kube_resource_type(self):
        return self._get_resource_name()

    def _read_namespaced_resource(self, name, namespace, **kwargs):
        read_func = getattr(self.client, 'read_namespaced_' + self._get_kube_resource_type())
        return read_func(name, namespace, **kwargs)

    def _list_resource_for_all_namespaces(self):
        list_func = getattr(self.client, 'list_%s_for_all_namespaces' % self._get_kube_resource_type())
        return list_func()

    @filecache(duration=60 * 60, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(True))

        if not self._have_resource_value():
            pod_name = self._get_one_resource_value('pod')
            namespace = self.client.get_namespace('pod', pod_name)
            result = self.client.read_namespaced_pod(pod_name, namespace)
            # for one_container in result.spec.containers:
            results.extend(self._get_completion([(one.name,one.image) for one in result.spec.containers], False))

        return '\n'.join(results)

    def list(self):
        ret = self._list_resource_for_all_namespaces()
        print(ret)

    def describe(self):
        pass

    def exec(self):
        container_name = self._get_one_resource_value()
        pod_name = self._get_one_resource_value("pod")
        namespace = self.client.get_namespace('pod', pod_name)

        self.client.exec('pod', pod_name, namespace, " ".join(self._get_action_params()), container_name)

    def download(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--local', help='local dir')
        parser.add_argument('--remote', help='remote dir')
        args = parser.parse_args(self._get_action_params())

        pod_name = self._get_one_resource_value('pod')
        container_name = self._get_one_resource_value()
        namespace = self.client.get_namespace('pod', pod_name)
        self.client.download(pod_name, namespace, args.local, args.remote, container_name)

    def upload(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--local', help='local dir')
        parser.add_argument('--remote', help='remote dir')
        args = parser.parse_args(self._get_action_params())

        container_name = self._get_one_resource_value()
        pod_name = self._get_one_resource_value('pod')
        namespace = self.client.get_namespace('pod', pod_name)
        self.client.upload(pod_name, namespace, args.local, args.remote, container_name)
