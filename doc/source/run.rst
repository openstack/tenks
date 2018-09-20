Running Tenks
=============

Commands
--------

Tenks has a variable ``cmd`` which specifies the command to be run. This
variable can be set in your override file (see :ref:`configuration`). The
possible values it can take are:

* ``deploy``: create a virtual cluster to the specification given. This is the
  default command.
* ``teardown``: tear down any existing virtual cluster with the specification
  given.

Execution
---------

Currently, Tenks does not have a CLI or wrapper. Deployment can be run by
calling ``ansible-playbook --inventory ansible/inventory ansible/deploy.yml
--extra-vars=@override.yml``, where ``override.yml`` is the path to your
override file.

The ``deploy.yml`` playbook will run deployment from start to finish;
``teardown.yml`` is ``deploy.yml``'s "mirror image" to tear down a cluster.
These playbooks automatically set ``cmd`` appropriately, and they contain
various constituent playbooks which perform different parts of the deployment.
An individual section of Tenks can be run separately by substituting
``ansible/deploy.yml`` in the command above with the path to the playbook(s)
you want to run. The current playbooks can be seen in the Ansible structure
diagram in :ref:`architecture`. Bear in mind that you will have to set
``cmd`` in your override file if you are running any of the sub-playbooks
individually.

Once a cluster has been deployed, it can be reconfigured by modifying the Tenks
configuration and rerunning ``deploy.yml``. Node specs can be changed
(including increasing/decreasing the number of nodes); node types can also be
reconfigured. Existing nodes will be preserved where possible.
