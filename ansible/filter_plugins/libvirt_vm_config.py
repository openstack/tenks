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

from ansible.errors import AnsibleFilterError
from jinja2 import contextfilter


class FilterModule(object):
    '''Libvirt configuration filters'''

    def filters(self):
        return {
            'set_libvirt_interfaces': set_libvirt_interfaces,
            'set_libvirt_volume_pool': set_libvirt_volume_pool,
        }


# Lifted from kayobe:ansible/filter_plugins/networks.py
def _get_hostvar(context, var_name, inventory_hostname=None):
    if inventory_hostname is None:
        namespace = context
    else:
        if inventory_hostname not in context['hostvars']:
            raise AnsibleFilterError(
                "Inventory hostname '%s' not in hostvars" % inventory_hostname)
        namespace = context["hostvars"][inventory_hostname]
    return namespace.get(var_name)


@contextfilter
def set_libvirt_interfaces(context, node):
    """Set interfaces for a node's specified physical networks.
    """
    physnet_mappings = _get_hostvar(context, 'physnet_mappings')
    prefix = _get_hostvar(context, 'veth_prefix')
    suffix = _get_hostvar(context, 'veth_node_source_suffix')

    node['interfaces'] = []
    # Libvirt doesn't need to know about physical networks, so pop them here.
    for physnet in node.pop('physical_networks', []):
        # Get the ID of this physical network on the hypervisor.
        idx = sorted(physnet_mappings).index(physnet)
        node['interfaces'].append(
            {'type': 'direct',
             # FIXME(w-miller): Don't duplicate the logic of this naming scheme
             # from node_physical_network.yml
             'source': {'dev': prefix + node['name'] + '-' + str(idx) +
                               suffix}}
        )
    return node


@contextfilter
def set_libvirt_volume_pool(context, node):
    """Set the Libvirt volume pool for each volume.
    """
    pool = _get_hostvar(context, 'libvirt_pool_name')
    for vol in node.get('volumes', []):
        vol['pool'] = pool
    return node
