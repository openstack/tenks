.. _installation:

Installation
============

.. _assumptions:

Assumptions
-----------

Some assumptions that are made about the configuration of your system are noted
below.

It is assumed that...

* ...you already have an OpenStack cloud deployed, for which...

  * ...the host from which Tenks is executed (*localhost*) has access to the
    OpenStack APIs. These are used for Ironic node enrolment and Nova flavor
    registration.

  * ...the OpenStack *OS_\** authentication variables are present in
    *localhost*'s environment. These can typically be sourced from your
    *openrc* file.

* ... a distinct network device (interface or bridge) is present for each
  physical network that a hypervisor is connected to.

Pre-Requisites
--------------

Currently, Tenks supports CentOS 7.5.

To avoid conflicts with Python packages installed by the system package manager
it is recommended to install Tenks in a virtualenv. Ensure that the
``virtualenv`` Python module is available. For cloning and working with the
Tenks source code repository, Git is required. These pre-requisites can be
installed with a command such as::

 $ yum install --assumeyes python-virtualenv git

 Open vSwitch must be installed and running. Please see the
 `Open vSwitch docs <https://docs.openvswitch.org/en/latest/intro/install/>`_
 for more details.

Tenks Installation
------------------

Create a virtualenv for Tenks. For example::

 $ virtualenv tenks

Activate the virtualenv and update pip::

 $ source tenks/bin/activate
 (tenks) $ pip install --upgrade pip

Obtain the Tenks source code and change into the directory. For example::

  (tenks) $ git clone https://opendev.org/openstack/tenks.git
  (tenks) $ cd tenks

Install Tenks and its requirements using the source code checkout::

  (tenks) $ pip install .

Tenks has dependencies on Ansible roles that are hosted by Ansible Galaxy.
These can be installed by a command such as::

  (tenks) $ ansible-galaxy install --role-file=requirements.yml --roles-path=ansible/roles/

If you now wish to run Tenks (see :ref:`run`), keep your virtualenv active. If
not, deactivate it::

  (tenks) $ deactivate
