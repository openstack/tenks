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

# Avoid shadowing of system copy module by copy action plugin.
from __future__ import absolute_import
import abc
from copy import deepcopy
import itertools

from ansible.errors import AnsibleActionFail
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
import six


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        """
        Produce a dict of Tenks state.

        Actions include:
            * Generating indices for physical networks for each hypervisor.
            * Scheduling specifications of nodes by type onto hypervisors.

        The following task arguments are accepted:
            :hypervisor_vars: A dict of hostvars for each hypervisor, keyed
                              by hypervisor hostname. Required.
            :specs: A list of node specifications to be instantiated. Required.
            :node_types: A dict mapping node type names to a dict of properties
                         of that type.
            :node_name_prefix: A string with which to prefix all sequential
                               node names.
            :vol_name_prefix: A string with which to prefix all sequential
                              volume names.
            :state: A dict of existing Tenks state (as produced by a previous
                    run of this module), to be taken into account in this run.
                    Optional.
            :prune_only: A boolean which, if set, will instruct the plugin to
                         only remove any nodes with state='absent' from
                         `state`.
        :returns: A dict of Tenks state for each hypervisor, keyed by the
                  hostname of the hypervisor to which the state refers.
        """
        result = super(ActionModule, self).run(tmp, task_vars)
        # Initialise our return dict.
        result['result'] = {}
        del tmp  # tmp no longer has any effect

        self.args = self._task.args
        self.localhost_vars = task_vars['hostvars']['localhost']
        self._validate_args()

        if self.args['prune_only']:
            self._prune_absent_nodes()
        else:
            # Modify the state as necessary.
            self._set_physnet_idxs()
            self._process_specs()

        # Return the modified state.
        result['result'] = self.args['state']
        return result

    def _prune_absent_nodes(self):
        """
        Remove any nodes with state='absent' from the state dict.
        """
        for hyp in six.itervalues(self.args['state']):
            hyp['nodes'] = [n for n in hyp['nodes']
                            if n.get('state') != 'absent']

    def _set_physnet_idxs(self):
        """
        Set the index of each physnet for each host.

        Use the specified physnet mappings and any existing physnet indices to
        ensure the generated indices are consistent.
        """
        state = self.args['state']
        for hostname, hostvars in six.iteritems(self.args['hypervisor_vars']):
            # The desired mappings given in the Tenks configuration. These do
            # not include IDXs which are an implementation detail of Tenks.
            specified_mappings = hostvars['physnet_mappings']
            try:
                # The physnet indices currently in the state file.
                old_idxs = state[hostname]['physnet_indices']
            except KeyError:
                # The hypervisor is new since the last run.
                state[hostname] = {}
                old_idxs = {}
            new_idxs = {}
            next_idx = 0
            used_idxs = list(six.itervalues(old_idxs))
            for name, dev in six.iteritems(specified_mappings):
                try:
                    # We need to re-use the IDXs of any existing physnets.
                    idx = old_idxs[name]
                except KeyError:
                    # New physnet requires a new IDX.
                    while next_idx in used_idxs:
                        next_idx += 1
                    used_idxs.append(next_idx)
                    idx = next_idx
                new_idxs[name] = idx
            state[hostname]['physnet_indices'] = new_idxs

    def _process_specs(self):
        """
        Ensure the correct nodes are present in `state`.

        Remove unnecessary nodes by marking as 'absent' and schedule new nodes
        to hypervisors such that the nodes in `state` match what's specified in
        `specs`.
        """
        # Iterate through existing nodes, marking for deletion where necessary.
        for hyp in six.itervalues(self.args['state']):
            # Absent nodes cannot fulfil a spec.
            for node in [n for n in hyp.get('nodes', [])
                         if n.get('state') != 'absent']:
                if ((self.localhost_vars['cmd'] == 'teardown' or
                     not self._tick_off_node(self.args['specs'], node))):
                    # We need to delete this node, since it exists but does not
                    # fulfil any spec.
                    node['state'] = 'absent'

        if self.localhost_vars['cmd'] != 'teardown':
            # Ensure all hosts exist in state.
            for hostname in self.args['hypervisor_vars']:
                self.args['state'].setdefault(hostname, {})
                self.args['state'][hostname].setdefault('nodes', [])
            # Now create all the required new nodes.
            scheduler = RoundRobinScheduler(self.args['hypervisor_vars'],
                                            self.args['state'])
            namer = Namer(self.args['state'])
            self._create_nodes(scheduler, namer)

    def _tick_off_node(self, specs, node):
        """
        Tick off an existing node as fulfilling a node specification.

        If `node` is required in `specs`, decrement that spec's count and
        return True. Otherwise, return False.
        """
        # Attributes that a spec and a node have to have in common for the node
        # to count as an 'instance' of the spec.
        MATCHING_ATTRS = {'type', 'ironic_config'}
        for spec in specs:
            if (all(spec.get(attr) == node.get(attr)
                    for attr in MATCHING_ATTRS)
                    and spec['count'] > 0):
                spec['count'] -= 1
                return True
        return False

    def _create_nodes(self, scheduler, namer):
        """
        Create new nodes to fulfil the specs.
        """
        # Anything left in specs needs to be created.
        for spec in self.args['specs']:
            for _ in six.moves.range(spec['count']):
                node = self._gen_node(spec['type'], spec.get('ironic_config'))
                hostname, ipmi_port = scheduler.choose_host(node)
                node_name_prefix = spec.get('node_name_prefix',
                                            self.args['node_name_prefix'])
                node['name'] = namer.get_name(node_name_prefix)
                # Sequentially number the volume names.
                vol_name_prefix = spec.get('vol_name_prefix',
                                           self.args['vol_name_prefix'])
                for vol_idx, vol in enumerate(node['volumes']):
                    vol['name'] = ("%s%s%d"
                                   % (node['name'], vol_name_prefix, vol_idx))
                node['ipmi_port'] = ipmi_port
                self.args['state'][hostname]['nodes'].append(node)

    def _gen_node(self, type_name, ironic_config=None):
        """
        Generate a node description.

        A name will not be assigned at this point because we don't know which
        hypervisor the node will be scheduled to.
        """
        node_type = self.args['node_types'][type_name]
        node = deepcopy(node_type)
        # All nodes need an Ironic driver.
        node.setdefault(
            'ironic_driver',
            self.localhost_vars['default_ironic_driver']
        )
        # Set the type name, for future reference.
        node['type'] = type_name
        # Ironic config is not mandatory.
        if ironic_config:
            node['ironic_config'] = ironic_config
        return node

    def _validate_args(self):
        if self.args is None:
            self.args = {}

        REQUIRED_ARGS = {'hypervisor_vars', 'specs', 'node_types'}
        # Var names and their defaults.
        OPTIONAL_ARGS = [
            ('node_name_prefix', 'tk'),
            # state is optional, since if this is the first run there won't be
            # any yet.
            ('state', {}),
            ('vol_name_prefix', 'vol'),
            ('prune_only', False),
        ]
        for arg in OPTIONAL_ARGS:
            if arg[0] not in self.args:
                self.args[arg[0]] = arg[1]

        # No arguments are required in prune_only mode.
        if not self.args['prune_only']:
            for arg in REQUIRED_ARGS:
                if arg not in self.args:
                    e = "The parameter '%s' must be specified." % arg
                    raise AnsibleActionFail(to_text(e))

            if not self.args['hypervisor_vars']:
                e = ("There are no hosts in the 'hypervisors' group to which "
                     "we can schedule.")
                raise AnsibleActionFail(to_text(e))

            for spec in self.args['specs']:
                if 'type' not in spec or 'count' not in spec:
                    e = ("All specs must contain a `type` and a `count`. "
                         "Offending spec: %s" % spec)
                    raise AnsibleActionFail(to_text(e))


class Namer(object):
    """
    Helper object for naming nodes with a prefix and index.
    """

    def __init__(self, state):
        self.existing_names = {node['name']
                               for hv_state in state.values()
                               for node in hv_state['nodes']
                               if node.get('state') != 'absent'}
        # Map from node name prefix to the next index to try.
        self.next_idxs = {}

    def get_name(self, node_name_prefix):
        """Return the next available name for the given prefix."""
        idx = self.next_idxs.setdefault(node_name_prefix, 0)
        while True:
            candidate = "%s%d" % (node_name_prefix, idx)
            if candidate not in self.existing_names:
                self.next_idxs[node_name_prefix] = idx + 1
                return candidate
            idx += 1


class Host(object):
    """
    Class representing a hypervisor host.
    """

    def __init__(self, hostname, hostvars, state):
        self.hostname = hostname
        self.physnet_mappings = hostvars['physnet_mappings']
        # Keep track of unused IPMI ports in the available range.
        free_ipmi_ports = set(
            range(hostvars['ipmi_port_range_start'],
                  hostvars['ipmi_port_range_end'] + 1))
        for node in state['nodes']:
            if node.get('state') != 'absent' and node['ipmi_port']:
                free_ipmi_ports.remove(node['ipmi_port'])
        self.free_ipmi_ports = sorted(free_ipmi_ports)

    def reserve(self):
        """
        Return the next available IPMI port for a node on this host.

        The port is also removed from the available ports.

        :returns: The next available IPMI port.
        """
        return self.free_ipmi_ports.pop(0)

    def host_passes(self, node):
        """
        Perform checks to ascertain whether this host can support this node.
        """
        # Is there a free IPMI port?
        if not self.free_ipmi_ports:
            return False
        # Check that the host is connected to all physical networks that the
        # node requires.
        return all(pn in self.physnet_mappings.keys()
                   for pn in node['physical_networks'])


@six.add_metaclass(abc.ABCMeta)
class Scheduler(object):
    """
    Abstract class representing a 'method' of scheduling nodes to hosts.
    """
    def __init__(self, hostvars, state):
        # Dict mapping a hypervisor hostname to a Host object for the
        # hypervisor.
        self.hosts = {hostname: Host(hostname, host_hv, state[hostname])
                      for hostname, host_hv in hostvars.items()}

    @abc.abstractmethod
    def choose_host(self, node):
        """Abstract method to choose a host to which we can schedule `node`.

        Returns a tuple of the hostname of the chosen host and the IPMI port
        for use by this node on the host.
        """
        raise NotImplementedError()


class RoundRobinScheduler(Scheduler):
    """
    Schedule nodes in a round-robin fashion to hosts.
    """
    def __init__(self, hostvars, state):
        super(RoundRobinScheduler, self).__init__(hostvars, state)
        self._host_cycle = itertools.cycle(self.hosts.keys())

    def choose_host(self, node):
        count = 0
        while True:
            # Ensure we don't get into an infinite loop if no hosts are
            # available.
            if count >= len(self.hosts):
                e = ("No hypervisors are left that can support the node %s."
                     % node)
                raise AnsibleActionFail(to_text(e))
            count += 1
            hostname = next(self._host_cycle)
            host = self.hosts[hostname]
            if host.host_passes(node):
                ipmi_port = host.reserve()
                return hostname, ipmi_port
