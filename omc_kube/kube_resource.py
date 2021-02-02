import json
import os
from datetime import datetime
import logging
from omc.core.decorator import filecache

from omc.config import settings
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from omc.common import CmdTaskMixin
from omc.core.resource import Resource
from omc.utils.file_utils import make_directory
from omc.utils.utils import get_obj_value, get_all_dict_Keys, set_obj_value, delete_obj_key


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

    def _list_resource_for_all_namespaces(self):
        list_func = getattr(self.client, 'list_%s_for_all_namespaces' % self._get_kube_api_resource_type())
        return list_func()

    def _get_resource(self):
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        return self._read_namespaced_resource(resource, namespace)

    def _get_namespace(self):
        resource = self._get_one_resource_value()
        return self.client.get_namespace(self._get_kube_api_resource_type(), resource)

    @filecache(duration=60 * 60, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(False))

        if not self._have_resource_value():
            ret = self._list_resource_for_all_namespaces()
            results.extend(
                self._get_completion([get_obj_value(one, 'metadata.name') for one in ret.get('items')], True))

        return "\n".join(results)

    def list(self):
        'display one or more resources'
        resource_name = self._get_one_resource_value()
        namespace = 'all' if not resource_name else self.client.get_namespace(self._get_kube_api_resource_type(),
                                                                              resource_name)

        # ret = self._list_resource_for_all_namespaces()
        # print(ret)
        result = self.client.get(self._get_kube_resource_type(), resource_name, namespace)
        print(result)

    def yaml(self):
        'get configuration in yaml format'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        stream = StringIO()
        yaml = YAML()
        yaml.dump(result, stream)
        print(stream.getvalue())

    def json(self):
        'get configuration by json format'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        print(json.dumps(result, default=dateconverter, indent=4))

    @staticmethod
    def _build_field_selector(selectors):
        return ','.join(['%s=%s' % (k, v) for (k, v) in selectors.items()])

    def namespace(self):
        'get resource namespace'
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        print(namespace)

    def event(self):
        'show event on the resource'
        # https://kubernetes.docker.internal:6443/api/v1/namespaces/default/events?fieldSelector=
        # involvedObject.uid=4bb31f4d-99f1-4acc-a024-8e2484573733,
        # involvedObject.name=itom-xruntime-rabbitmq-6464654786-vnjxz,
        # involvedObject.namespace=default

        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)

        uid = get_obj_value(result, 'metadata.uid')
        name = get_obj_value(result, 'metadata.name')

        the_selector = {
            "involvedObject.uid": uid,
            "involvedObject.namespace": namespace,
            "involvedObject.name": name,
        }

        print(self.client.list_namespaced_event(namespace, field_selector=self._build_field_selector(the_selector)))

    def _get_config_key_cache_file_name(self):
        main_path = [one for one in self.context['all'][1:] if not one.startswith('-')]
        cache_file = os.path.join(settings.OMC_COMPLETION_CACHE_DIR, *main_path)
        return cache_file

    @filecache(duration=60 * 5, file=_get_config_key_cache_file_name)
    def _get_config_key_completion(self):
        resource = self._get_one_resource_value()
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
        result = self._read_namespaced_resource(resource, namespace)
        prompts = []
        get_all_dict_Keys(result.to_dict(), prompts)
        return '\n'.join(self._get_completion(prompts))

    # def get(self):
    #     'get resource by configuration key'
    #     if 'completion' in self._get_params():
    #         completion = self._get_config_key_completion()
    #         print(completion)
    #         return
    #
    #     resource = self._get_one_resource_value()
    #     namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
    #     result = self._read_namespaced_resource(resource, namespace)
    #     params = self._get_action_params()
    #
    #     the_params = " ".join(params)
    #
    #     if not the_params.strip():
    #         print(result)
    #     else:
    #         print(get_obj_value(result, the_params))
    #
    # def set(self):
    #     'update restore by configuration key'
    #     if 'completion' in self._get_params():
    #         resource = self._get_one_resource_value()
    #         namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
    #         result = self._read_namespaced_resource(resource, namespace)
    #         prompts = []
    #         get_all_dict_Keys(result.to_dict(), prompts)
    #         self._print_completion(prompts)
    #         return
    #
    #     resource = self._get_one_resource_value()
    #     namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
    #     result = self._read_namespaced_resource(resource, namespace)
    #     params = self._get_action_params()
    #     config_key = params[0]
    #     config_value = params[1]
    #     orig_value = get_obj_value(result, config_key)
    #     # convert type
    #     config_value = type(orig_value)(config_value)
    #     set_obj_value(result, config_key, config_value)
    #
    #     # todo: use apply instead once apply provided
    #     new_result = self.client.replace_namespaced_deployment(resource, namespace, result)
    #     print(get_obj_value(new_result, config_key))
    #
    # def delete(self):
    #     'delete node by configuration key'
    #     # todo@rain: to support delete entired resource and completion cache
    #     if 'completion' in self._get_params():
    #         resource = self._get_one_resource_value()
    #         namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
    #         result = self._read_namespaced_resource(resource, namespace)
    #         prompts = []
    #         get_all_dict_Keys(result.to_dict(), prompts)
    #         self._print_completion(prompts)
    #         return
    #
    #     resource = self._get_one_resource_value()
    #     namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
    #     result = self._read_namespaced_resource(resource, namespace)
    #     params = self._get_action_params()
    #     config_key = params[0]
    #     # convert type
    #     delete_obj_key(result, config_key)
    #
    #     # todo: use apply instead once apply provided
    #     new_result = self.client.replace_namespaced_deployment(resource, namespace, result)

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
        delete_obj_key(the_result, 'metadata.creationTimestamp')
        delete_obj_key(the_result, 'metadata.resourceVersion')
        delete_obj_key(the_result, 'metadata.annotations')
        delete_obj_key(the_result, 'metadata.managedFields')
        delete_obj_key(the_result, 'metadata.uid')
        delete_obj_key(the_result, 'metadata.selfLink')
        delete_obj_key(the_result, 'metadata.generation')
        delete_obj_key(the_result, 'status')
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

        print(self.client.describe(self._get_kube_resource_type(), resource_name, namespace))

    def relations(self):
        pass
