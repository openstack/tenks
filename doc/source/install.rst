Installation
===============

Tenks has dependencies on Ansible roles that are hosted by Ansible Galaxy.
Given that your virtualenv of choice is active and Ansible (>=2.6) is
installed inside it, Tenks' role dependencies can be installed by
``ansible-galaxy install --role-file=requirements.yml
--roles-path=ansible/roles/``.
