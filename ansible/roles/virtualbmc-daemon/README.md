Virtual BMC Daemon
==================

This role sets up the Virtual BMC daemon in systemd.

Requirements
------------

- systemd

Role Variables
--------------

- `vbmcd_virtualenv_path`: The path to the virtualenv in which to install
  Virtual BMC.
- `vbmcd_python_upper_constraints_url`: The URL of the upper constraints file
  to pass to pip when installing Python packages.
