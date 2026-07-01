Sushy Redfish
=============

This role sets up a Sushy Redfish Emulator.

Requirements
------------

- libvirt-python

Role Variables
--------------

- `sushy_tools_virtualenv_path`: The path to the virtualenv in which to install
  sushy-tools. Must have libvirt-python installed in it.
- `sushy_python_upper_constraints_url`: The URL of the upper constraints file
  to pass to pip when installing Python packages.
- `sushy_allowed_nodes`: The identities of the nodes that the sushy-emulator
  is allowed to manage.
- `sushy_redfish_address`: The IP address that the sushy-emulator listens on.
- `sushy_log_directory`: The directory in which to store sushy-emulator logs.
  Optional.
- `sushy_libvirt_uri`: The URI used to connect to libvirt. Optional.