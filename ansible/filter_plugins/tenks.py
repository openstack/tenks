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
import math
import re
import six

from ansible.errors import AnsibleFilterError
from ansible.module_utils._text import to_text
from jinja2 import contextfilter


class FilterModule(object):
    '''Tenks filters

    NOTE(w-miller): The Libvirt filters need to use some of the network name
    filters. Due to Ansible issue #27748, filter plugins cannot import any
    custom Python modules, so we can't have a Libvirt filters file that imports
    a network filters file; for the same reason, we can't have a shared utils
    file either. This is why all Tenks filters are lumped together in this
    file.
    '''

    def filters(self):
        return {
            # Network name filters.
            'bridge_name': bridge_name,
            'ovs_link_name': ovs_link_name,
            'source_link_name': source_link_name,
            'source_to_ovs_link_name': source_to_ovs_link_name,
            'source_link_to_physnet_name': source_link_to_physnet_name,

            # Libvirt filters.
            'set_libvirt_interfaces': set_libvirt_interfaces,
            'set_libvirt_volume_pool': set_libvirt_volume_pool,

            # Miscellaneous filters.
            'size_string_to_gb': size_string_to_gb,
        }


# Lifted from kayobe:ansible/filter_plugins/networks.py
def _get_hostvar(context, var_name, inventory_hostname=None):
    if inventory_hostname is None:
        namespace = context
    else:
        if inventory_hostname not in context['hostvars']:
            raise AnsibleFilterError(
                "Inventory hostname '%s' not in hostvars" % inventory_hostname)
        namespace = context['hostvars'][inventory_hostname]
    return namespace.get(var_name)


@contextfilter
def set_libvirt_interfaces(context, node):
    """Set interfaces for a node's specified physical networks.
    """
    node['interfaces'] = []
    for physnet in node.get('physical_networks', []):
        node['interfaces'].append(
            {'type': 'direct',
             'source': {'dev': source_link_name(context, node, physnet)}}
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


@contextfilter
def bridge_name(context, physnet):
    """Get the Tenks OVS bridge name from a physical network name.
    """
    return (_get_hostvar(context, 'bridge_prefix') +
            str(_physnet_name_to_index(context, physnet)))


@contextfilter
def source_link_name(context, node, physnet):
    """Get the source veth link name for a node/physnet combination.
    """
    return (_link_name(context, node, physnet) +
            _get_hostvar(context, 'veth_node_source_suffix'))


@contextfilter
def ovs_link_name(context, node, physnet):
    """Get the OVS veth link name for a node/physnet combination.
    """
    return (_link_name(context, node, physnet) +
            _get_hostvar(context, 'veth_node_ovs_suffix'))


@contextfilter
def source_to_ovs_link_name(context, source):
    """Get the corresponding OVS link name for a source link name.
    """
    base = source[:-len(_get_hostvar(context, 'veth_node_source_suffix'))]
    return base + _get_hostvar(context, 'veth_node_ovs_suffix')


@contextfilter
def source_link_to_physnet_name(context, source):
    """ Get the physical network name that a source veth link is connected to.
    """
    prefix = _get_hostvar(context, 'veth_prefix')
    suffix = _get_hostvar(context, 'veth_node_source_suffix')
    match = re.compile(r"%s.*-(\d+)%s"
                       % (re.escape(prefix), re.escape(suffix))).match(source)
    idx = match.group(1)
    return _physnet_index_to_name(context, int(idx))


def size_string_to_gb(size):
    """
    Parse a size string, and convert to the integer number of GB it represents.
    """
    return int(math.ceil(_parse_size_string(size) / 10**9))


def _parse_size_string(size):
    """
    Parse a capacity string.

    Takes a string representing a capacity and returns the size in bytes, as an
    integer. Accepts strings such as "5", "5B", "5g", "5GB", " 5  GiB ", etc.
    Case insensitive. See `man virsh` for more details.

    :param size: The size string to parse.
    :returns: The number of bytes represented by `size`, as an integer.
    """
    # Base values for units.
    BIN = 1024
    DEC = 1000
    POWERS = {"": 0, "k": 1, "m": 2, "g": 3, "t": 4}
    # If an integer is passed, treat it as a string without units.
    size = str(size).lower()
    regex = r"\s*(\d+)\s*([%s])?(i?b)?\s*$" % "".join(POWERS.keys())
    match = re.compile(regex).match(size)
    if not match:
        msg = "The size string '%s' is not of a valid format." % size
        raise AnsibleFilterError(to_text(msg))
    number = match.group(1)
    power = match.group(2)
    unit = match.group(3)
    if not power:
        power = ""
    if unit == "b":
        base = DEC
    else:
        base = BIN
    return int(number) * (base ** POWERS[power])


def _link_name(context, node, physnet):
    prefix = _get_hostvar(context, 'veth_prefix')
    return prefix + node['name'] + '-' + str(_physnet_name_to_index(context,
                                                                    physnet))


def _physnet_name_to_index(context, physnet):
    """Get the ID of this physical network on the hypervisor.
    """
    physnet_mappings = _get_hostvar(context, 'physnet_mappings')
    return sorted(physnet_mappings).index(physnet)


def _physnet_index_to_name(context, idx):
    """Get the name of this physical network on the hypervisor.
    """
    physnet_mappings = _get_hostvar(context, 'physnet_mappings')
    return sorted(physnet_mappings)[idx]
