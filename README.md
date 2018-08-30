Tenks
=====

Tenks is a utility that manages virtual bare metal clusters for development and
testing purposes.

Getting Started
---------------

Tenks has dependencies on Ansible roles that are hosted by Ansible Galaxy.
Given that your virtualenv of choice is active and Ansible (>=2.6) is
installed inside it, Tenks' role dependencies can be installed by
`ansible-galaxy install --role-file=requirements.yml
--roles-path=ansible/roles/`.

Currently, Tenks does not have a CLI or wrapper. A virtual cluster can be
deployed by configuring the variables defined in `group_vars/*` as necessary,
then calling `ansible-playbook --inventory ansible/inventory ansible/deploy.yml`.
