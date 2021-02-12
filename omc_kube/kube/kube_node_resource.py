import json
import os
from datetime import datetime

import pkg_resources

from omc.core.decorator import filecache

from omc.config import settings
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from omc.common import CmdTaskMixin
from omc.core.resource import Resource
from omc.utils import utils
from omc.utils.file_utils import make_directory
from omc.utils.utils import get_obj_value, get_all_dict_Keys, set_obj_value, delete_obj_key

from omc_kube.core import StrategicMergePatch


def dateconverter(o):
    if isinstance(o, datetime):
        return o.__str__()


class KubeNodeResource(Resource, CmdTaskMixin):
    def __init__(self, context={}, type='web'):
        super().__init__(context, type)
        self.client = self.context['common']['client']

    def _get_kube_resource_type(self):
        return self._get_parent_resource_name()

    def _get_kube_api_resource_type(self):
        return self._get_parent_resource_name()

    def _read_namespaced_resource(self, name, namespace, **kwargs):
        read_func = getattr(self.client, 'read_namespaced_' + self._get_kube_api_resource_type())
        return read_func(name, namespace, **kwargs)

    def _list_resource_for_all_namespaces(self):
        list_func = getattr(self.client, 'list_%s_for_all_namespaces' % self._get_kube_api_resource_type())
        return list_func()

    @filecache(duration=60 * 60, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(False))

        if not self._have_resource_value():
            # parent_resource = self._get_one_resource_value(self._get_kube_resource_type())
            # namespace = self.client.get_namespace(self._get_kube_api_resource_type(), parent_resource)

            kube_resource_type = self._get_kube_resource_type()
            completion_file_name = pkg_resources.resource_filename('omc_kube.%(kube_resource_type)s' % locals(), '_%(kube_resource_type)s_completion.json' % locals())
            prompts = []
            # get_all_dict_Keys(result.to_dict(), prompts)
            with open(completion_file_name) as f:
                result = json.load(f)
                get_all_dict_Keys(result, prompts)
                results.extend(self._get_completion(prompts))

        return "\n".join(results)

    @staticmethod
    def _build_field_selector(selectors):
        return ','.join(['%s=%s' % (k, v) for (k, v) in selectors.items()])

    def get(self):
        'get resource by configuration key'
        parent_resource = self._get_one_resource_value(self._get_kube_resource_type())
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), parent_resource)
        result = self._read_namespaced_resource(parent_resource, namespace)

        # config resource is the item
        resource = self._get_one_resource_value()

        if not resource:
            print(result)
        else:
            print(get_obj_value(result, resource))

    def set(self):
        'update restore by configuration key'
        # https://github.com/kubernetes/kubernetes/blob/cea1d4e20b4a7886d8ff65f34c6d4f95efcb4742/staging/src/k8s.io/apimachinery/pkg/util/strategicpatch/patch.go
        # implement Strategic merge patch myself
        # https://stackoverflow.com/questions/36307950/kubernetes-api-call-equivalent-to-kubectl-apply
        if 'completion' in self._get_params():
            resource = self._get_one_resource_value()
            namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
            result = self._read_namespaced_resource(resource, namespace)
            prompts = []
            get_all_dict_Keys(result.to_dict(), prompts)
            self._print_completion(prompts)
            return

        config_key = self._get_one_resource_value()
        parent_resource = self._get_one_resource_value(self._get_kube_resource_type())
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), parent_resource)
        result = self._read_namespaced_resource(parent_resource, namespace)
        params = self._get_action_params()
        config_value = params[0]
        orig_value = get_obj_value(result, config_key)
        # convert type
        config_value = type(orig_value)(config_value)
        set_obj_value(result, config_key, config_value)

        # todo: use apply instead once apply provided
        patch_func = getattr(self.client, 'patch_namespaced_' + self._get_kube_api_resource_type())
        # patch_object = utils.build_object(config_key, config_value)
        patch_object = StrategicMergePatch.get_instance().gen_strategic_merge_patch(result, config_key.split('.'),
                                                                                    config_value, 'set', [])
        new_result = patch_func(parent_resource, namespace, patch_object)
        print(new_result)

    def delete(self):
        'delete node by configuration key'
        # todo@rain: to support delete entired resource and completion cache
        if 'completion' in self._get_params():
            resource = self._get_one_resource_value()
            namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)
            result = self._read_namespaced_resource(resource, namespace)
            prompts = []
            get_all_dict_Keys(result.to_dict(), prompts)
            self._print_completion(prompts)
            return

        config_key = self._get_one_resource_value()
        parent_resource = self._get_one_resource_value(self._get_kube_resource_type())
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), parent_resource)
        the_result = self._read_namespaced_resource(parent_resource, namespace, _preload_content=False)
        result = json.loads(the_result.data.decode('UTF-8'))
        params = self._get_action_params()
        config_value = params[0] if len(params) > 0 else None
        # orig_value = get_obj_value(result, config_key)
        # # convert type
        # config_value = type(orig_value)(config_value)
        # set_obj_value(result, config_key, config_value)

        # todo: use apply instead once apply provided
        patch_func = getattr(self.client, 'patch_namespaced_' + self._get_kube_api_resource_type())
        # patch_object = utils.build_object(config_key, config_value)
        patch_object = StrategicMergePatch.get_instance().gen_strategic_merge_patch(result, config_key.split('.'),
                                                                                    config_value, 'delete', [])
        new_result = patch_func(parent_resource, namespace, patch_object)
        print(new_result)

    def _edit(self):
        'Edit a resource from the default editor.'
        resource = self._get_one_resource_value(self._get_kube_resource_type())
        namespace = self.client.get_namespace(self._get_kube_api_resource_type(), resource)

        self.client.edit(self._get_kube_resource_type(), resource, namespace)

    def _save(self):
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
        yaml = YAML()
        yaml.dump(the_result, stream)
        content = stream.getvalue()

        make_directory(cache_folder)
        with open(os.path.join(cache_folder, resource_name + '.yaml'), 'w') as f:
            f.write(content)

    def _restore(self):
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
        if os.path.exists(config_file):
            self.client.apply(config_file)
        else:
            raise Exception("no config file found")

if __name__ ==  '__main__':
    resource = pkg_resources.resource_filename('omc_kube.deployment', '_deployment_completion.json')
    print(resource)