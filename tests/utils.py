import json

import unittest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

# Python 2/3 compatibility.
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch  # noqa


def set_module_args(args):
    if '_ansible_remote_tmp' not in args:
        args['_ansible_remote_tmp'] = '/tmp'
    if '_ansible_keep_remote_files' not in args:
        args['_ansible_keep_remote_files'] = False

    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class ModuleTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ModuleTestCase, self).__init__(*args, **kwargs)
        # Python 2 / 3 compatibility. assertRaisesRegexp was renamed to
        # assertRaisesRegex in python 3.1.
        if hasattr(self, 'assertRaisesRegexp') and \
                not hasattr(self, 'assertRaisesRegex'):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        self.mock_module = patch.multiple(basic.AnsibleModule,
                                          exit_json=exit_json,
                                          fail_json=fail_json)
        self.mock_module.start()
        set_module_args({})
        self.addCleanup(self.mock_module.stop)
