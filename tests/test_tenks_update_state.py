# Copyright (c) 2018 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
import imp
import os
import sys

import unittest

# Python 2/3 compatibility.
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock


# Import method lifted from kolla_ansible's test_merge_config.py
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
PLUGIN_FILE = os.path.join(PROJECT_DIR,
                           'ansible/action_plugins/tenks_update_state.py')

tus = imp.load_source('tenks_update_state', PLUGIN_FILE)

class TestTenksUpdateState(unittest.TestCase):
    def setUp(self):
        # Pass dummy arguments to allow instantiation of action plugin.
        self.mod = tus.ActionModule(None, None, None, None, None, None)

        # Minimal inputs required.
        self.node_types = {
            'type0': {
                'memory_mb': 1024,
                'vcpus': 2,
                'volumes': [
                    {
                        'capacity': '10GB',
                    },
                ],
                'physical_networks': [
                    'physnet0',
                ],
            },
        }
        self.specs = [
            {
                'type': 'type0',
                'count': 2,
                'ironic_config': {
                    'resource_class': 'testrc',
                },
            },
        ]
        self.hypervisor_vars = {
            'foo': {
                'physnet_mappings': {
                    'physnet0': 'dev0',
                },
                'ipmi_port_range_start': 100,
                'ipmi_port_range_end': 102,
            },
        }

    def test__set_physnet_idxs_no_state(self):
        state = {}
        self.mod._set_physnet_idxs(state, self.hypervisor_vars)
        expected_indices = {
            'physnet0': 0,
        }
        self.assertEqual(state['foo']['physnet_indices'], expected_indices)
