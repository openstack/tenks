Virtual BMC Domain
==================

This role ensures a Libvirt domain is added to and started in Virtual BMC.

Requirements
------------

- Virtual BMC installed in a virtualenv
- Virtual BMC daemon running

Role Variables
--------------

- `vbmc_domain`: The name of the Libvirt domain to be added to Virtual BMC.
- `vbmc_virtualenv_path`: The path to the virtualenv in which Virtual BMC is
  installed.
- `vbmc_ipmi_listen_address`: The address on which Virtual BMC will listen for
  IPMI traffic. Default is 0.0.0.0.
- `vbmc_ipmi_port`: The port on which Virtual BMC will listen for IPMI traffic.
  Default is 6230.
- `vbmc_ipmi_username`: The IPMI username that Virtual BMC will use. Default is
  'username'.
- `vbmc_ipmi_password`: The IPMI password that Virtual BMC will use. Default is
  'password'.
- `vbmc_log_directory`: The directory in which to store Virtual BMC logs. If
   `None`, output will not be logged to a file. Default is `None`.
