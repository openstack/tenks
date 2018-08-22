# Avoid shadowing of system copy module by copy action plugin.
from __future__ import absolute_import
from copy import deepcopy
import operator

from ansible.errors import AnsibleActionFail
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
from six import iteritems


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        """
        Schedule specifications of VMs by flavour onto hypervisors.

        The following task vars are accepted:
            :hypervisor_vars: A dict of hostvars for each hypervisor, keyed
                              by hypervisor hostname. Required.
            :specs: A dict mapping flavour names to the number of VMs
                    required of that flavour. Required.
            :flavours: A dict mapping flavour names to a dict of properties
                       of that flavour.
            :vm_name_prefix: A string with with to prefix all sequential VM
                             names.
            :vol_name_prefix: A string with with to prefix all sequential
                              volume names.
        :returns: A dict containing lists of VM details, keyed by the
                  hostname of the hypervisor to which they are scheduled.
        """
        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        self._validate_vars(task_vars)

        vms = []
        idx = 0
        for flav, cnt in iteritems(task_vars['specs']):
            for _ in xrange(cnt):
                vm = deepcopy(task_vars['flavours'][flav])
                # Sequentially number the VM and volume names.
                vm['name'] = "%s%d" % (task_vars['vm_name_prefix'], idx)
                for vol_idx, vol in enumerate(vm['volumes']):
                    vol['name'] = "%s%d" % (task_vars['vol_name_prefix'],
                                            vol_idx)
                vms.append(vm)
                idx += 1

        # TODO(w-miller): currently we just arbitrarily schedule all VMs to the
        # first hypervisor. Improve this algorithm to make it more
        # sophisticated.
        result['result'] = {task_vars['hypervisor_vars'].keys()[0]: vms}
        return result

    def _validate_vars(self, task_vars):
        if task_vars is None:
            task_vars = {}

        REQUIRED_TASK_VARS = {'hypervisor_vars', 'specs', 'flavours'}
        # Var names and their defaults.
        OPTIONAL_TASK_VARS = {
            ('vm_name_prefix', 'vm'),
            ('vol_name_prefix', 'vol'),
        }
        for var in REQUIRED_TASK_VARS:
            if var not in task_vars:
                e = "The parameter '%s' must be specified." % var
                raise AnsibleActionFail(to_text(e))

        for var in OPTIONAL_TASK_VARS:
            if var[0] not in task_vars:
                task_vars[var[0]] = var[1]

        if not task_vars['hypervisor_vars']:
            e = ("There are no hosts in the 'hypervisors' group to which we "
                 "can schedule.")
            raise AnsibleActionFail(to_text(e))
