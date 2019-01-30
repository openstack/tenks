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
import copy
import imp
import os

from ansible.errors import AnsibleActionFail
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
            'state': {},
            'vol_name_prefix': 'test_vol_pfx',
        }
        # Alias for brevity.
        self.args = self.mod.args

    def test__set_physnet_idxs_no_state(self):
        self.mod._set_physnet_idxs()
        expected_indices = {
            'physnet0': 0,
        }
        self.assertEqual(self.args['state']['foo']['physnet_indices'],
                         expected_indices)

    def test__set_physnet_idxs_no_state_two_hosts(self):
        self.hypervisor_vars['bar'] = self.hypervisor_vars['foo']
        self.mod._set_physnet_idxs()
        expected_indices = {
            'physnet0': 0,
        }
        for hyp in {'foo', 'bar'}:
            self.assertEqual(self.args['state'][hyp]['physnet_indices'],
                             expected_indices)

    def test_set_physnet_idxs__no_state_two_hosts_different_nets(self):
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
                self.assertIn(node['name'] + 'test_vol_pfx' + n,
                              [vol['name'] for vol in node['volumes']])
            for c in {'10GB', '20GB'}:
                self.assertIn(c, [vol['capacity'] for vol in node['volumes']])

    def test__process_specs_apply_twice(self):
        self.mod._process_specs()
        created_state = copy.deepcopy(self.args['state'])
        self.mod._process_specs()
        self.assertEqual(created_state, self.args['state'])

    def test__process_specs_multiple_hosts(self):
        self.hypervisor_vars['bar'] = self.hypervisor_vars['foo']
        self.mod._process_specs()
        foo_nodes = self.args['state']['foo']['nodes']
        bar_nodes = self.args['state']['bar']['nodes']
        names = {foo_nodes[0]['name'], bar_nodes[0]['name']}
        self.assertEqual(names, {'test_node_pfx0', 'test_node_pfx1'})

    def test__process_specs_unnecessary_node(self):
        # Create some nodes definitions.
        self.mod._process_specs()

        # Add another node to the state that isn't required.
        self.args['state']['foo']['nodes'].append(copy.deepcopy(
            self.args['state']['foo']['nodes'][0]))
        self.args['state']['foo']['nodes'][-1]['vcpus'] = 42
        new_node = copy.deepcopy(self.args['state']['foo']['nodes'][-1])

        self.mod._process_specs()
        # Check that node has been marked for deletion.
        self.assertNotIn(new_node, self.args['state']['foo']['nodes'])
        new_node['state'] = 'absent'
        self.assertIn(new_node, self.args['state']['foo']['nodes'])

    def test__process_specs_teardown(self):
        # Create some node definitions.
        self.mod._process_specs()

        # After teardown, we expected all created definitions to now have an
        # 'absent' state.
        expected_state = copy.deepcopy(self.args['state'])
        for node in expected_state['foo']['nodes']:
            node['state'] = 'absent'
        self.mod.localhost_vars['cmd'] = 'teardown'

        # After one or more runs, the 'absent' state nodes should still exist,
        # since they're only removed after completion of deployment in a
        # playbook.
        for _ in six.moves.range(3):
            self.mod._process_specs()
            self.assertEqual(expected_state, self.args['state'])

    def test__process_specs_no_hypervisors(self):
        self.args['hypervisor_vars'] = {}
        self.assertRaises(AnsibleActionFail, self.mod._process_specs)

    def test__process_specs_no_hypervisors_on_physnet(self):
        self.node_types['type0']['physical_networks'].append('another_pn')
        self.assertRaises(AnsibleActionFail, self.mod._process_specs)

    def test__process_specs_one_hypervisor_on_physnet(self):
        self.node_types['type0']['physical_networks'].append('another_pn')
        self.hypervisor_vars['bar'] = copy.deepcopy(
            self.hypervisor_vars['foo'])
        self.hypervisor_vars['bar']['physnet_mappings']['another_pn'] = 'dev1'
        self.mod._process_specs()

        # Check all nodes were scheduled to the hypervisor connected to the
        # new physnet.
        self.assertEqual(len(self.args['state']['foo']['nodes']), 0)
        self.assertEqual(len(self.args['state']['bar']['nodes']), 2)

    def test__process_specs_not_enough_ports(self):
        # Give 'foo' only a single IPMI port to allocate.
        self.hypervisor_vars['foo']['ipmi_port_range_start'] = 123
        self.hypervisor_vars['foo']['ipmi_port_range_end'] = 123
        self.assertRaises(AnsibleActionFail, self.mod._process_specs)

    def test__process_specs_node_name_prefix(self):
        self.specs[0]['node_name_prefix'] = 'foo-prefix'
        self.mod._process_specs()
        foo_nodes = self.args['state']['foo']['nodes']
        self.assertEqual(foo_nodes[0]['name'], 'foo-prefix0')
        self.assertEqual(foo_nodes[1]['name'], 'foo-prefix1')

    def test__process_specs_node_name_prefix_multiple_specs(self):
        self.specs[0]['node_name_prefix'] = 'foo-prefix'
        self.specs.append({
            'type': 'type0',
            'count': 1,
            'ironic_config': {
                'resource_class': 'testrc',
            },
        })
        self.mod._process_specs()
        foo_nodes = self.args['state']['foo']['nodes']
        self.assertEqual(foo_nodes[0]['name'], 'foo-prefix0')
        self.assertEqual(foo_nodes[1]['name'], 'foo-prefix1')
        self.assertEqual(foo_nodes[2]['name'], 'test_node_pfx0')

    def test__process_specs_node_name_prefix_multiple_hosts(self):
        self.specs[0]['node_name_prefix'] = 'foo-prefix'
        self.hypervisor_vars['bar'] = self.hypervisor_vars['foo']
        self.mod._process_specs()
        foo_nodes = self.args['state']['foo']['nodes']
        bar_nodes = self.args['state']['bar']['nodes']
        names = {foo_nodes[0]['name'], bar_nodes[0]['name']}
        self.assertEqual(names, {'foo-prefix0', 'foo-prefix1'})

    def test__process_specs_vol_name_prefix(self):
        self.specs[0]['vol_name_prefix'] = 'foo-prefix'
        self.mod._process_specs()
        foo_nodes = self.args['state']['foo']['nodes']
        self.assertEqual(foo_nodes[0]['volumes'][0]['name'],
                         'test_node_pfx0foo-prefix0')
        self.assertEqual(foo_nodes[0]['volumes'][1]['name'],
                         'test_node_pfx0foo-prefix1')
        self.assertEqual(foo_nodes[1]['volumes'][0]['name'],
                         'test_node_pfx1foo-prefix0')
        self.assertEqual(foo_nodes[1]['volumes'][1]['name'],
                         'test_node_pfx1foo-prefix1')

    def test__prune_absent_nodes(self):
        # Create some node definitions.
        self.mod._process_specs()
        # Set them to be 'absent'.
        for node in self.args['state']['foo']['nodes']:
            node['state'] = 'absent'
        self.mod._prune_absent_nodes()
        # Ensure they were removed.
        self.assertEqual(self.args['state']['foo']['nodes'], [])
