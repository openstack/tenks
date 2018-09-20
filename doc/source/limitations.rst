Limitations
===========

The following is a non-exhaustive list of current known limitations of Tenks:

* When using the Libvirt provider (currently the only provider), Tenks
  hypervisors cannot co-exist with a containerised Libvirt daemon (for example,
  as deployed by Kolla in the nova-libvirt container). Tenks will configure an
  uncontainerised Libvirt daemon instance on the hypervisor, and this may
  conflict with an existing containerised daemon. A workaround is to disable
  the Nova virtualised compute service on each Tenks hypervisor if it is
  present (for example, ``docker stop nova_libvirt``) before running Tenks.
