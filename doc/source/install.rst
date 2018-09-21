.. _installation:

Installation
============

Pre-Requisites
--------------

Currently, Tenks supports CentOS 7.5.

To avoid conflicts with Python packages installed by the system package manager
it is recommended to install Tenks in a virtualenv. Ensure that the
``virtualenv`` Python module is available. For cloning and working with the
Tenks source code repository, Git is required. These pre-requisites can be
installed with a command such as::

 $ yum install --assumeyes python-virtualenv git

Tenks Installation
------------------

Create a virtualenv for Tenks. For example::

 $ virtualenv tenks

Activate the virtualenv and update pip::

 $ source tenks/bin/activate
 (tenks) $ pip install --upgrade pip

Obtain the Tenks source code and change into the directory. For example::

  (tenks) $ git clone https://github.com/stackhpc/tenks.git
  (tenks) $ cd tenks

Tenks has dependencies on Ansible roles that are hosted by Ansible Galaxy.
These can be installed by a command such as::

  (tenks) $ ansible-galaxy install --role-file=requirements.yml --roles-path=ansible/roles/

Install Tenks and its requirements using the source code checkout::

  (tenks) $ pip install .

If you now wish to run Tenks (see :ref:`run`), keep your virtualenv active. If
not, deactivate it::

  (tenks) $ deactivate
