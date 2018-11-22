Development
===========

To-Do List
----------

The following is a non-exhaustive list of features that are on the wishlist
to be implemented in future.

* **More providers**. It would be useful to extend Tenks to support providers
  other than Libvirt/QEMU/KVM - for example, VirtualBox, VMware or OpenStack.

* **More platform management systems**. Redfish is gaining momentum in the
  Ironic community as an alternative to IPMI-over-LAN, so adding support for
  this to Tenks would widen its appeal. This would involve adding support for
  configuration of a Redfish BMC emulator, such as that which `sushy-tools
  <https://github.com/openstack/sushy-tools>`__ offers.

* **Increased networking complexity**. As described in :ref:`assumptions`,
  making the assumption that each network to which nodes are connected will
  have a physical counterpart imposes some limitations. For example, if a
  hypervisor has fewer interfaces than physical networks exist in Tenks, either
  one or more physical networks will not be usable by nodes on that hypervisor,
  or multiple networks will have to share the same interface, breaking network
  isolation.

  It would be useful for Tenks to support more complex software-defined
  networking. This could allow multiple 'physical networks' to safely share the
  same physical link on a hypervisor. VLAN tagging is used by certain OpenStack
  networking drivers (networking-generic-switch, for example) to provide tenant
  isolation for instance traffic. While this in itself is outside of the scope
  of Tenks, it would need to be taken into account if VLANs were also used for
  network separation in Tenks, due to potential gotchas when using nested
  VLANs.

* **More intelligent scheduling**. The current system used to choose a
  hypervisor to host each node is rather naïve: it uses a round-robin approach
  to cycle through the hypervisors. If the next hypervisor in the cycle is not
  able to host the node, it will check the others as well. However, the
  incorporation of more advanced scheduling heuristics to inform more optimal
  placement of nodes would be desirable. All of Ansible's gathered facts about
  each hypervisor are available to the scheduling plugin, so it would be
  relatively straightforward to use facts about total/available memory or CPU
  load to shift the load balance towards more capable hypervisors.

* **Command-line interface**. Currently, Tenks must be called by an
  ``ansible-playbook`` invocation with multiple parameters. It would be less
  clunky to introduce a simple CLI wrapper encapsulating some default commands.

* **Configurable boot modes**. Support for boot modes other than legacy BIOS
  (for example, UEFI) would be useful. OpenStack Ironic supports configuration
  of boot modes with the `boot_mode` parameter for certain drivers. The
  Libvirt/QEMU/KVM stack supports UEFI boot with the `OVMF project
  <http://www.linux-kvm.org/downloads/lersek/ovmf-whitepaper-c770f8c.txt>`__

Contribution
------------

Contribution to Tenks' development is welcomed. Tenks uses the `OpenStack
development processes
<https://docs.openstack.org/infra/manual/developers.html>`__. Code reviews
should be submitted to `Gerrit
<https://review.openstack.org/#/q/project:openstack/tenks>`__, and bugs and
RFEs submitted to `StoryBoard
<https://storyboard.openstack.org/#!/project/openstack/tenks>`__.
