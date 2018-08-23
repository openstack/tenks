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
    veth_suffix = _get_hostvar(context, 'veth_vm_source_suffix')
    vm['interfaces'] = []
    for veth_base_name in vm['veths']:
        vm['interfaces'].append(
            {'type': 'direct',
             'source': {'dev': veth_base_name + veth_suffix}}
        )
    return vm


@contextfilter
def set_libvirt_volume_pool(context, vm):
    """Set the Libvirt volume pool for each volume.
    """
    pool = _get_hostvar(context, 'libvirt_pool_name')
    for vol in vm.get('volumes', []):
        vol['pool'] = pool
