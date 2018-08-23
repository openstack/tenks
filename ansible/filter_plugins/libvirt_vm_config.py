from ansible.errors import AnsibleFilterError
from ansible.module_utils._text import to_text
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
            raise errors.AnsibleFilterError(
                "Inventory hostname '%s' not in hostvars" % inventory_hostname)
        namespace = context["hostvars"][inventory_hostname]
    return namespace.get(var_name)


@contextfilter
def set_libvirt_interfaces(context, vm):
    """Set interfaces for a VM's specified physical networks.
    """
    physnet_mappings = _get_hostvar(context, 'physnet_mappings')
    prefix = _get_hostvar(context, 'veth_prefix')
    suffix = _get_hostvar(context, 'veth_vm_source_suffix')

    vm['interfaces'] = []
    # Libvirt doesn't need to know about physical networks, so pop them here.
    for physnet in vm.pop('physical_networks', []):
        # Get the ID of this physical network on the hypervisor.
        idx = sorted(physnet_mappings).index(physnet)
        vm['interfaces'].append(
            {'type': 'direct',
             # FIXME(w-miller): Don't duplicate the logic of this naming scheme
             # from vm_physical_network.yml
             'source': {'dev': prefix + vm['name'] + '-' + str(idx) + suffix}}
        )
    return vm


@contextfilter
def set_libvirt_volume_pool(context, vm):
    """Set the Libvirt volume pool for each volume.
    """
    pool = _get_hostvar(context, 'libvirt_pool_name')
    for vol in vm.get('volumes', []):
        vol['pool'] = pool
    return vm
