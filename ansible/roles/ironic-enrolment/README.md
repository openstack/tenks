Ironic Enrolment
================

This role enrols nodes with OpenStack Ironic, creates Ironic ports for each of
the nodes' NICs, and sets relevant attributes on created resources.

Requirements
------------

- *OS_\** environment variables for the OpenStack cloud in question present in
  the shell environment. These can be sourced from an OpenStack RC file, for
  example.

- The `virsh` command-line tool present at `/usr/bin/virsh`.

Role Variables
--------------

- `ironic_nodes`: A list of dicts of details for nodes that are to be enroled
  in Ironic.
- `ironic_hypervisor`: The hostname of the hypervisor on which `ironic_nodes`
  exist.
- `ironic_deploy_kernel_uuid`: The Glance UUID of the image to use for the
  deployment kernel.
- `ironic_deploy_ramdisk_uuid`: The Glance UUID of the image to use for the
  deployment ramdisk.
- `ironic_virtualenv_path`: The path to the virtualenv in which to install the
  OpenStack clients.
- `ironic_python_upper_constraints_url`: The URL of the upper constraints file
  to pass to pip when installing Python packages.
