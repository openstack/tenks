# Copyright (c) 2026 StackHPC Ltd.
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

from importlib import util as imp_util
import os
import unittest


def load_module(name, path):
    module_spec = imp_util.spec_from_file_location(
        name, path
    )
    module = imp_util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
PLUGIN_FILE = os.path.join(PROJECT_DIR, 'ansible/filter_plugins/tenks.py')

filters = load_module('tenks_filters', PLUGIN_FILE)


class TestSetLibvirtInterfaces(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.context = {
            'inventory_hostname': 'foo',
            'veth_prefix': 'p-',
            'veth_node_source_suffix': '-tap',
            'hostvars': {
                'localhost': {
                    'tenks_state': {
                        'foo': {
                            'physnet_indices': {
                                'physnet0': 0,
                                'physnet1': 1,
                            },
                        },
                    },
                },
            },
        }
        self.node = {
            'name': 'tk0',
            'physical_networks': ['physnet0', 'physnet1'],
        }

    def test_set_libvirt_interfaces(self):
        node = filters.set_libvirt_interfaces(self.context, self.node)
        interfaces = node['interfaces']
        self.assertEqual(2, len(interfaces))
        for idx, iface in enumerate(interfaces):
            self.assertEqual('direct', iface['type'])
            self.assertEqual({'dev': 'p-tk00-%d-tap' % idx,
                              'mode': 'passthrough'}, iface['source'])
            self.assertRegex(iface['mac'],
                             r'^52:54:00(:[0-9a-f]{2}){3}$')
        self.assertNotEqual(interfaces[0]['mac'], interfaces[1]['mac'])

    def test_set_libvirt_interfaces_mac_stable(self):
        node1 = filters.set_libvirt_interfaces(self.context, dict(self.node))
        node2 = filters.set_libvirt_interfaces(self.context, dict(self.node))
        self.assertEqual(node1['interfaces'], node2['interfaces'])

    def test_set_libvirt_interfaces_mac_unique_per_node(self):
        node1 = filters.set_libvirt_interfaces(self.context, dict(self.node))
        other = dict(self.node, name='tk1')
        node2 = filters.set_libvirt_interfaces(self.context, other)
        self.assertNotEqual(node1['interfaces'][0]['mac'],
                            node2['interfaces'][0]['mac'])
