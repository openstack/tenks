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
then calling
`ansible-playbook --inventory ansible/inventory ansible/deploy.yml`. Individual
sections of Tenks can be run separately by substituting `ansible/deploy.yml` in
the command above with the path to the playbook you want to run. The current
playbooks can be seen in the Ansible structure diagram in the *Development*
section.

Development
-----------

A diagram representing the Ansible structure of Tenks can be seen below. Blue
rectangles represent playbooks, green rounded rectangles represent task books,
red ellipses represent roles and yellow rhombi represent action plugins.

<!---
This diagram will need to be updated when the Ansible structure changes. The
original draw.io diagram can be found below. The link below contains the
diagram's XML which can be imported into draw.io and edited, then a new PNG
artifact can be produced.

https://drive.google.com/file/d/1MlmaTvJ2BPkhrOCLin4GPH265JDJqD1E/view?usp=sharing
-->

![Tenks Ansible structure](assets/tenks_ansible_structure.png)
