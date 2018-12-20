.. _configuration:

Configuration
=============

Hosts
-----

Tenks uses Ansible inventory to manage hosts. A multi-host setup is therefore
supported, although the default hosts configuration will deploy an all-in-one
setup on the host where the ``ansible-playbook`` command is executed
(*localhost*).

* Configuration management of the Tenks cluster is always performed on
  *localhost*.
* The ``hypervisors`` group should not directly contain any hosts. Its sub-groups
  must contain one or more system. Systems in its sub-groups will host a subset
  of the nodes deployed by Tenks.

  * The ``libvirt`` group is a sub-group of ``hypervisors``. Systems in this
    group will act as hypervisors using the Libvirt provider.

Variable Configuration
----------------------

A variable override file should be created to configure Tenks. Any variables
specified in this file will take precedence over their default settings in
Tenks. This will allow you to set options as necessary for your setup, without
needing to directly modify Tenks' variable files. An example override file can
be found in ``ansible/override.yml.example``.

Most of the configuration you will need to do relates to variables defined in
``ansible/host_vars/localhost``. You can set your own values for these in your
override file (mentioned above). In addition to other options, you will need to
define the types of node you'd like to be able to manage as a dict in
``node_types``, as well as the desired deployment specifications in ``specs``.
Format and guidance for available options will be found within the variable
file.

Broadly, most variables in ``ansible/group_vars/*`` have sensible defaults
which may be left as-is unless you have a particular need to configure them. A
notable exception to this is the variable ``physnet_mappings`` in
``ansible/group_vars/hypervisors``, which should map physical network names to
the device to use for that network: this can be a network interface, or an
existing OVS or Linux bridge. If these mappings are the same for all hosts in
your ``hypervisors`` group, you may set a single dict ``physnet_mappings`` in
your overrides file, and this will be used for all hosts. If different mappings
are required for different hosts, you will need to individually specify them in
an inventory host_vars file: for a host with hostname *myhost*, set
``physnet_mappings`` within the file ``ansible/inventory/host_vars/myhost``.

Standalone Ironic
-----------------

In standalone ironic environments, the placement service is typically not
available. To prevent Tenks from attempting to communicate with placement, set
``wait_for_placement`` to ``false``.

It is likely that a standalone ironic environment will not use authentication
to access the ironic API. In this case, it is possible to set the ironic API
URL via ``clouds.yaml``. For example:

.. code-block:: yaml

   ---
   clouds:
     standalone:
       auth_type: "none"
       endpoint: http://localhost:6385

Then set the ``OS_CLOUD`` environment variable to ``standalone``.
