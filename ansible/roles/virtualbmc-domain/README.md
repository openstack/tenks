Virtual BMC Domain
==================

This role configures a Libvirt domain in Virtual BMC. If `vbmc_state` is
`present`, it will ensure the domain is added and started; if `vbmc_state` is
`absent`, it will ensure the domain is stopped and deleted.

Requirements
------------

- Virtual BMC installed in a virtualenv
- Virtual BMC daemon running

Role Variables
--------------

- `vbmc_domain`: The name of the Libvirt domain to be added to Virtual BMC.
- `vbmc_virtualenv_path`: The path to the virtualenv in which Virtual BMC is
  installed.
- `vbmc_ipmi_address`: The address on which Virtual BMC will listen for IPMI
  traffic.
- `vbmc_ipmi_port`: The port on which Virtual BMC will listen for IPMI traffic.
- `vbmc_ipmi_username`: The IPMI username that Virtual BMC will use.
- `vbmc_ipmi_password`: The IPMI password that Virtual BMC will use.
- `vbmc_log_directory`: The directory in which to store Virtual BMC logs. If
   not overridden from `None`, output will not be logged to a file.
- `vbmc_state`: Whether the domain should be `present` or `absent` in Virtual
  BMC. Defaults to `present`.
