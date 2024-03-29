import json
import os
import re
from datetime import datetime
import logging

from omc.common.common_completion import completion_cache, CompletionContent
from omc.common.formatter import Formatter
from omc.core import console
from omc.core.decorator import filecache, resource_instance_action, resource_class_action

from omc.config import settings
from omc.utils.object_utils import ObjectUtils
from ruamel_yaml import YAML
from ruamel_yaml.compat import StringIO

from omc.common import CmdTaskMixin
from omc.core.resource import Resource
from omc.utils.file_utils import make_directory


def dateconverter(o):
    if isinstance(o, datetime):
        return o.__str__()


class KubeResource(Resource, CmdTaskMixin):
    def __init__(self, context={}, type='web'):
        super().__init__(context, type)
        self.client = self.context['common']['client']

    def _get_kube_resource_type(self):
        return self._get_resource_name()

    def _get_kube_api_resource_type(self):
        # specified for python api,
        # same as resource type by default
        # but some resource type is slight different configmap -> config_map
        return self._get_resource_name()

    def _read_namespaced_resource(self, name, namespace, **kwargs):
        read_func = getattr(self.client, 'read_namespaced_' + self._get_kube_api_resource_type())
        return read_func(name, namespace, **kwargs)

    def _list_resource_for_all_namespaces(self, *args, **kwargs):
        list_func = getattr(self.client, 'list_%s_for_all_namespaces' % self._get_kube_api_resource_type())
        return list_func(*args, **kwargs)

    def _get_resource(self):
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        return self._read_namespaced_resource(resource, namespace)

    def _get_namespace(self):
        resource = self._get_one_resource_value()
        return self.client.get_namespace(self._get_kube_api_resource_type(), resource)

    def _resource_completion(self, short_mode=True):
        output = self.client.get(self._get_kube_api_resource_type(), timeout=3)

        results = []

        for one in output.splitlines():
            # for case like: 'itsma-j6zm1 smarta-sawmeta-dih- 172.16.0.84:31371,172.16.0.84:1444,172.16.0.84:1445  3 more...          4d3h'
            # one = re.sub(' \+ \d+ more...', '...', one)
            one_line = one.strip().split(None, maxsplit=3)
            one_line[0],one_line[1] = one_line[1],one_line[0]
            results.append(one_line)

        # ret = self._list_resource_for_all_namespaces(timeout_seconds=settings.COMPETION_TIMEOUT)
        # results.extend(
        #     self._get_completion([ObjectUtils.get_node(one, 'metadata.name') for one in ret.get('items')], True))

        return CompletionContent(Formatter.format_completions(results))

    @resource_class_action
    def list(self):
        'display one or more resources'
        resource_name = self._get_one_resource_value()
        namespace = 'all' if not resource_name else self.client.get_namespace(self._get_kube_api_resource_type(),
                                                                              resource_name)

        # ret = self._list_resource_for_all_namespaces()
        # console.log(ret)
        result = self.client.get(self._get_kube_resource_type(), resource_name, namespace)
        console.log(result)

    @resource_instance_action
    def yaml(self):
        'get configuration in yaml format'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        stream = StringIO()
        yaml = YAML()
        yaml.dump(result, stream)
        console.log(stream.getvalue())

    @resource_instance_action
    def json(self):
        'get configuration by json format'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        console.log(json.dumps(result, default=dateconverter, indent=4))

    @staticmethod
    def _build_field_selector(selectors):
        return ','.join(['%s=%s' % (k, v) for (k, v) in selectors.items()])


    def namespace(self):
        'get resource namespace'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        console.log(namespace)

    def event(self):
        'show event on the resource'
        # https://kubernetes.docker.internal:6443/api/v1/namespaces/default/events?fieldSelector=
        # involvedObject.uid=4bb31f4d-99f1-4acc-a024-8e2484573733,
        # involvedObject.name=itom-xruntime-rabbitmq-6464654786-vnjxz,
        # involvedObject.namespace=default

        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)

        uid = ObjectUtils.get_node(result, 'metadata.uid')
        name = ObjectUtils.get_node(result, 'metadata.name')

        the_selector = {
            "involvedObject.uid": uid,
            "involvedObject.namespace": namespace,
            "involvedObject.name": name,
        }

        console.log(
            self.client.list_namespaced_event(namespace, field_selector=self._build_field_selector(the_selector)))

    def _get_config_key_cache_file_name(self):
        main_path = [one for one in self.context['all'][1:] if not one.startswith('-')]
        cache_file = os.path.join(settings.OMC_COMPLETION_CACHE_DIR, *main_path)
        return cache_file

    @completion_cache(duration=60 * 5, file=_get_config_key_cache_file_name)
    def _get_config_key_completion(self):
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        prompts = []
        ObjectUtils.get_nodes(result.to_dict(), prompts)
        return CompletionContent(self._get_completion(prompts))

    def edit(self):
        'Edit a resource from the default editor.'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)

        self.client.edit(self._get_kube_resource_type(), resource, namespace)

    def save(self):
        'save configuration in file cache to be restored'
        resource_name = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)
        kube_instance = self._get_one_resource_value("kube")
        if not kube_instance:
            kube_instance = 'local'
        cache_folder = os.path.join(settings.OMC_KUBE_CACHE_DIR, kube_instance, namespace,
                                    self._get_kube_resource_type())

        result = self._read_namespaced_resource(resource_name, namespace, _preload_content=False)
        stream = StringIO()
        the_result = json.loads(result.data.decode('UTF-8'))
        ObjectUtils.delete_node(the_result, 'metadata.creationTimestamp')
        ObjectUtils.delete_node(the_result, 'metadata.resourceVersion')
        ObjectUtils.delete_node(the_result, 'metadata.annotations')
        ObjectUtils.delete_node(the_result, 'metadata.managedFields')
        ObjectUtils.delete_node(the_result, 'metadata.uid')
        ObjectUtils.delete_node(the_result, 'metadata.selfLink')
        ObjectUtils.delete_node(the_result, 'metadata.generation')
        ObjectUtils.delete_node(the_result, 'status')
        yaml = YAML()
        yaml.dump(the_result, stream)
        content = stream.getvalue()

        make_directory(cache_folder)
        config_file = os.path.join(cache_folder, resource_name + '.yaml')
        logging.info('save %s %s to %s' % (self._get_kube_resource_type(), resource_name, config_file))
        with open(config_file, 'w') as f:
            f.write(content)

    def restore(self):
        'restore configuration saved in file cache'
        resource_name = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)
        kube_instance = self._get_one_resource_value("kube")
        if not kube_instance:
            kube_instance = 'local'
        cache_folder = os.path.join(settings.OMC_KUBE_CACHE_DIR, kube_instance, namespace,
                                    self._get_kube_resource_type())
        make_directory(cache_folder)

        config_file = os.path.join(cache_folder, resource_name + '.yaml')

        logging.info('restore %s %s from %s' % (self._get_kube_resource_type(), resource_name, config_file))
        if os.path.exists(config_file):
            self.client.apply(config_file)
        else:
            raise Exception("config file %s not found" % config_file)

    def exec(self):
        'Execute a command in a container'
        resource_name = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)

        self.client.exec(self._get_kube_resource_type(), resource_name, namespace, " ".join(self._get_action_params()))

    def describe(self):
        'Show details of a specific resource or group of resources'
        resource_name = self._get_one_resource_value()
        namespace = 'all'
        if resource_name:
            namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource_name)

        console.log(self.client.describe(self._get_kube_resource_type(), resource_name, namespace))

    def relations(self):
        pass
