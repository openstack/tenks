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

import six
import unittest

# Python 2/3 compatibility.
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock # noqa


# Import method lifted from kolla_ansible's test_merge_config.py
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
PLUGIN_FILE = os.path.join(PROJECT_DIR,
                           'ansible/action_plugins/tenks_update_state.py')

tus = imp.load_source('tenks_update_state', PLUGIN_FILE)


class TestTenksUpdateState(unittest.TestCase):
    def setUp(self):
        # Pass dummy arguments to allow instantiation of action plugin.
        self.mod = tus.ActionModule(None, None, None, None, None, None)
        self.mod.localhost_vars = {
            'cmd': 'deploy',
            'default_ironic_driver': 'def_ir_driv',
        }

        # Minimal inputs required.
        self.node_types = {
            'type0': {
                'memory_mb': 1024,
                'vcpus': 2,
                'volumes': [
                    {
                        'capacity': '10GB',
                    },
                    {
                        'capacity': '20GB',
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
        self.mod.args = {
            'hypervisor_vars': self.hypervisor_vars,
            'node_types': self.node_types,
            'node_name_prefix': 'test_node_pfx',
            'specs': self.specs,
            'vol_name_prefix': 'test_vol_pfx',
        }
        # Alias for brevity.
        self.args = self.mod.args

    def test__set_physnet_idxs_no_state(self):
        self.args['state'] = {}
        self.mod._set_physnet_idxs()
        expected_indices = {
            'physnet0': 0,
        }
        self.assertEqual(self.args['state']['foo']['physnet_indices'],
                         expected_indices)

    def test__set_physnet_idxs_no_state_two_hosts(self):
        self.args['state'] = {}
        self.hypervisor_vars['bar'] = self.hypervisor_vars['foo']
        self.mod._set_physnet_idxs()
        expected_indices = {
            'physnet0': 0,
        }
        for hyp in {'foo', 'bar'}:
            self.assertEqual(self.args['state'][hyp]['physnet_indices'],
                             expected_indices)

    def test_set_physnet_idxs__no_state_two_hosts_different_nets(self):
        self.args['state'] = {}
        self.hypervisor_vars['bar'] = self.hypervisor_vars['foo']
        self.hypervisor_vars['foo']['physnet_mappings'].update({
            'physnet1': 'dev1',
            'physnet2': 'dev2',
        })
        self.hypervisor_vars['bar']['physnet_mappings'].update({
            'physnet2': 'dev2',
        })
        self.mod._set_physnet_idxs()
        for host in {'foo', 'bar'}:
            idxs = list(six.itervalues(
                self.args['state'][host]['physnet_indices']))
            # Check all physnets have different IDs on the same host.
            six.assertCountEqual(self, idxs, set(idxs))

    def test_set_physnet_idxs__idx_maintained_after_removal(self):
        self.args['state'] = {}
        self.hypervisor_vars['foo']['physnet_mappings'].update({
            'physnet1': 'dev1',
        })
        self.mod._set_physnet_idxs()
        physnet1_idx = self.args['state']['foo']['physnet_indices']['physnet1']
        del self.hypervisor_vars['foo']['physnet_mappings']['physnet0']
        self.mod._set_physnet_idxs()
        self.assertEqual(
            physnet1_idx,
            self.args['state']['foo']['physnet_indices']['physnet1']
        )

    def _test__process_specs_no_state_create_nodes(self):
        self.args['state'] = {}
        self.mod._process_specs()
        self.assertEqual(len(self.args['state']['foo']['nodes']), 2)
        return self.args['state']['foo']['nodes']

    def test__process_specs_no_state_attrs(self):
        nodes = self._test__process_specs_no_state_create_nodes()
        for node in nodes:
            self.assertTrue(node['name'].startswith('test_node_pfx'))
            self.assertEqual(node['memory_mb'], 1024)
            self.assertEqual(node['vcpus'], 2)
            self.assertEqual(node['physical_networks'], ['physnet0'])

    def test__process_specs_no_state_ipmi_ports(self):
        nodes = self._test__process_specs_no_state_create_nodes()
        used_ipmi_ports = set()
        for node in nodes:
            self.assertGreaterEqual(
                node['ipmi_port'],
                self.hypervisor_vars['foo']['ipmi_port_range_start']
            )
            self.assertLessEqual(
                node['ipmi_port'],
                self.hypervisor_vars['foo']['ipmi_port_range_end']
            )
            self.assertNotIn(node['ipmi_port'], used_ipmi_ports)
            used_ipmi_ports.add(node['ipmi_port'])

    def test__process_specs_no_state_volumes(self):
        nodes = self._test__process_specs_no_state_create_nodes()
        for node in nodes:
            self.assertEqual(len(node['volumes']), 2)
            for n in {'0', '1'}:
                self.assertIn('test_vol_pfx' + n,
                              [vol['name'] for vol in node['volumes']])
            for c in {'10GB', '20GB'}:
                self.assertIn(c, [vol['capacity'] for vol in node['volumes']])
