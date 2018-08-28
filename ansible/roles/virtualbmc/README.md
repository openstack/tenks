Virtual BMC
===========

This role sets up Virtual BMC. It will configure the Virtual BMC daemon in
systemd, and add the specified domains to the daemon.

Requirements
------------

- systemd

Role Variables
--------------

- `vbmc_libvirt_domains`: A list of Libvirt domain names to be added to Virtual
  BMC.
- `vbmc_ipmi_listen_address`: The address on which Virtual BMC will listen for
  IPMI traffic.
- `vbmc_ipmi_port_range_start`, `vbmc_ipmi_port_range_end`: The range of ports
  available for use by Virtual BMC.
- `vbmc_ipmi_username`: The IPMI username that Virtual BMC will use.
- `vbmc_ipmi_password`: The IPMI password that Virtual BMC will use.
- `vbmc_log_directory`: The directory in which to store Virtual BMC logs.
- `vbmc_virtualenv_path`: The path to the virtualenv in which to install
  Virtual BMC.
