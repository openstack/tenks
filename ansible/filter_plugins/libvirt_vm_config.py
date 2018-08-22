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
    veth_prefix = _get_hostvar(context, 'veth_prefix')
    veth_    = _get_hostvar(context, 'veth_base_name')


    vm['interfaces'] = []
    physnets = vm.pop('physical_networks', [])
    for physnet in physnets:
        try:
            vm['interfaces'].append(
                {'type': 'direct',
                 'source': {'dev': physnet_mappings[physnet]}}
            )
        except KeyError:
            raise AnsibleFilterError(to_text(
                "No interface mapping was specified for physical network "
                "'%s'." % physnet
            ))
     return vm


def set_libvirt_volume_pool(vm, volume_pool):
    """
    Set the Libvirt volume pool for each volume.

    :param vm: A VM definiton.
    :param volume_pool: The name of the Libvirt volume pool to use.
    """
    for vol in vm.get('volumes', []):
        vol['pool'] = volume_pool
