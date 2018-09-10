Nova Flavors
============

This role manages flavors in Nova. If `flavors_state` is `present`, it will
ensure the specified flavors eexist; if it is `absent`, it will ensure they do
not.

Requirements
------------

- *OS_\** environment variables for the OpenStack cloud in question present in
  the shell environment. These can be sourced from an OpenStack RC file, for
  example.

Role Variables
--------------

- `flavors`: A list of dicts of details for flavors that are to be created. The
  format for this is detailed in `defaults/main.yml`.
- `flavors_virtualenv_path`: The path to the virtualenv in which to install the
  OpenStack clients.
- `flavors_python_upper_constraints_url`: The URL of the upper constraints file
  to pass to pip when installing Python packages.
- `flavors_state`: Whether the specified flavors should be `present` or
 `absent`. Default is `present`.
