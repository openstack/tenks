#!/usr/bin/python

# Copyright (c) 2018 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

DOCUMENTATION = """
module: wait_for_resources
short_description: Waits for a set of resources to become available in
placement
author: Will Szumski(will@stackhpc.com)
options:
  - option-name: resources
    description: List of dictionaries describing the resources that should
    be available. Each dictionary should contain the keys: resource_class,
    amount, and optionally, a list of traits that the provider needs to provide
    before it is considered to provide the resource.
    required: True
    type: list
  - option-name: venv
    description: Path to a virtualenv containing the OpenStack CLI. It is a
    requirement for the placement api plugin (osc-placement) to be installed.
    required: False
    type: string
  - option-name: maximum_retries
    description: The maximum number of iterations to poll for the resources
    required: False
    type: int
  - option-name: delay
    description: Delay between each iteration of the polling loop in seconds
    required: False
    type: int
requirements:
  - python-openstackclient
  - osc-placement
"""

EXAMPLES = """
- name: Wait for resources to become available
  wait_for_resources:
    resources: {'resource_class: CUSTOM_TEST_RC, 'traits': [], 'amount': 2}
    delay: 10
    maximum_retries: 15
    venv: /path/to/venv
"""

RETURN = """
iterations:
  description: The Number of iterations required before the resource became
  available
  returned: success
  type: int
  sample: 9
"""

# Need to disable PEP8, as it wants all imports at top of file
from ansible.module_utils.basic import AnsibleModule  # noqa
from collections import namedtuple  # noqa
import six  # noqa
import os  # noqa
import time  # noqa

_RETRY_LIMIT_FAILURE_TEMPLATE = "exceeded retry limit of {max_retries} " \
                                "whilst waiting for resources to become " \
                                "available"

Specifier = namedtuple("Specifier", "name traits")
Provider = namedtuple("Provider", "uuid inventory_list traits")

# Store a list of import errors to report to the user.
IMPORT_ERRORS = []
try:
    import json
except Exception as e:
    IMPORT_ERRORS.append(e)


def meets_criteria(actual, requested):
    """For each resource, determines whether the total satisfies the amount
    requested, ignoring any unrequested resource_classes"""
    for specifier in requested.keys():
        if specifier not in actual:
            return False
        if actual[specifier] < requested[specifier]:
            return False
    return True


def get_openstack_binary_path(module):
    """Returns the path to the openstack binary taking into account the
    virtualenv that was specified (if available)"""
    venv = module.params["venv"]
    if venv:
        return os.path.join(venv, "bin", "openstack")
    # use openstack in PATH
    return "openstack"


def get_inventory(module, provider_uuid):
    """
    Gets inventory of resources for a give provider UUID
    :param module: ansible module
    :param provider_uuid: provider to query
    :return: list of dictionaries of the form:
    [
      {
        "allocation_ratio": 16.0,
        "total": 24,
        "reserved": 0,
        "resource_class": "VCPU",
        "step_size": 1,
        "min_unit": 1,
        "max_unit": 24
      },
    ]
    """
    cmd = "{openstack} resource provider inventory list {uuid} -f json" \
        .format(uuid=provider_uuid,
                openstack=get_openstack_binary_path(module))

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "{} failed with return code: {}, stderr: {}".format(cmd, rc, err)
        module.fail_json(msg=msg)
    return json.loads(out)


def get_providers(module):
    """
    Gets a list of resource providers
    :param module: ansible module
    :return: list of dictionaries of the form:
    [
      {
        "generation": 2,
        "uuid": "657c4ab0-de82-4def-b7b0-d13ce672bfd0",
        "name": "kayobe-will-master"
      },
    ]
    """
    cmd = "{openstack} resource provider list -f json".format(
        openstack=get_openstack_binary_path(module)
    )
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "{} failed with return code: {}, stderr: {}".format(cmd, rc, err)
        module.fail_json(msg=msg)
    return json.loads(out)


def get_traits(module, provider_uuid):
    """
    Gets a list of traits for a resource provider
    :param provider_uuid: the uuid of the provider
    :param module: ansible module
    :return: set of traits of the form:
    {
        "HW_CPU_X86_SSE2",
    }
    """
    cmd = "{openstack} resource provider trait list {uuid} " \
          "--os-placement-api-version 1.6 -f json " \
        .format(uuid=provider_uuid,
                openstack=get_openstack_binary_path(module))

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        msg = "{} failed with return code: {}, stderr: {}".format(cmd, rc, err)
        module.fail_json(msg=msg)
    raw = json.loads(out)
    return set([x["name"] for x in raw])


def merge(x, y, f):
    """ Merges two dictionaries. If a key appears in both dictionaries, the
    common values are merged using the function ``f``"""
    # Start with symmetric difference; keys either in A or B, but not both
    merged = {k: x.get(k, y.get(k)) for k in six.viewkeys(x) ^ six.viewkeys(y)}
    # Update with `f()` applied to the intersection
    merged.update(
        {k: f(x[k], y[k]) for k in six.viewkeys(x) & six.viewkeys(y)})
    return merged


def collect(module, specifiers, provider):
    """Given a specifier and a provider, gets the amount of resource that is
     available for that given provider"""
    inventory = {}

    # we want to be able to look up items by resource_class
    for item in provider.inventory_list:
        inventory[item["resource_class"]] = item
    result = {}
    module.debug("Collecting from a provider with the following traits: {}"
                 .format(provider.traits))
    for specifier in specifiers:
        if specifier.traits != provider.traits:
            module.debug("Provider can't provide {}, as the following traits "
                         "did not fully match: {}"
                         .format(specifier.name, specifier.traits))
            continue
        if specifier.name in inventory:
            reserved = inventory[specifier.name]["reserved"]
            total_available = inventory[specifier.name]["total"]
            excess = total_available - reserved
            result[specifier] = excess
            module.debug("Excess resources for {}: {}".format(specifier.name,
                                                              excess))
            break
        else:
            module.debug("{} not in inventory for provider: {}"
                         .format(specifier.name, provider.uuid))
    return result


def get_totals(module, specifiers, providers):
    """Loops over the providers adding up all of the resources that
    are available"""
    totals = {}

    for specifier in specifiers:
        # initialise totals so the combine function does not blow up
        totals[specifier] = 0

    for provider in providers:
        current = collect(module, specifiers, provider)
        totals = merge(totals, current, lambda x, y: x + y)

    return totals


def are_resources_available(module, specifiers, expected):
    """
    Determines whether or not a set of resources are available
    :param module: Ansible module
    :param specifiers: tuples of the form: (resource_class, traits)
    :param expected: dictionary of the form:
    {(resource_class, traits): amount }
    :return: True if resource available, otherwise False
    """
    providers_raw = get_providers(module)
    providers = []
    for provider in providers_raw:
        uuid = provider["uuid"]
        traits = get_traits(module, uuid)
        # Don't include traits assigned by the nova compute driver.
        traits = {t for t in traits if not t.startswith('COMPUTE_')}
        inventory = get_inventory(module, uuid)
        provider = Provider(
            uuid=uuid,
            inventory_list=inventory,
            traits=traits
        )
        providers.append(provider)
    actual = get_totals(module, specifiers, providers)
    return meets_criteria(actual, expected)


def wait_for_resources(module):
    """
    Waits for a set of resources to become available
    :param module: Ansible module
    :return: the number of attempts needed
    """
    max_retries = module.params["maximum_retries"]
    delay = module.params["delay"]
    resources = module.params["resources"]
    expected = {}
    specifiers = []
    for resource in resources:
        # default value for traits
        traits = resource["traits"] if resource["traits"] else []
        specifier = Specifier(name=resource["resource_class"],
                              traits=frozenset(traits))
        specifiers.append(specifier)
        expected[specifier] = resource["amount"]

    for i in range(max_retries):
        if are_resources_available(module, specifiers, expected):
            return i + 1
        time.sleep(delay)

    fail_msg = _RETRY_LIMIT_FAILURE_TEMPLATE.format(
        max_retries=max_retries)
    module.fail_json(msg=fail_msg)


def validate_spec(module, resource, field, type_):
    check_resource_msg = (
        "Please check the dictionaries in your resources list meet the "
        "required specification.")
    unset_field_msg = (
        "One of your resources does not have the field, {field}, set."
    )
    field_type_msg = (
        "The field, {field}, should be type {type}."
    )
    if field not in resource:
        msg = "{} {}".format(unset_field_msg, check_resource_msg)
        module.fail_json(msg=msg.format(field=field))
    elif not isinstance(resource[field], type_):
        msg = "{} {}".format(field_type_msg, check_resource_msg)
        module.fail_json(msg=msg.format(field=field, type=type_.__name__))


def validate_resources(module, specs):
    resources = module.params["resources"]
    for resource in resources:
        for spec in specs:
            validate_spec(module, resource, spec["field"], type_=spec["type"])


def get_module():
    """Creates and returns an Ansible module"""
    module = AnsibleModule(
        argument_spec=dict(
            resources=dict(required=True, type='list'),
            maximum_retries=dict(required=False, type='int', default=15),
            delay=dict(required=False, type='int', default=10),
            venv=dict(required=False, type='str', default="")
        ),
        supports_check_mode=True,
    )

    # note(wszumski): amount seems to get converted back to a string
    # https://github.com/ansible/ansible/issues/18095
    resources = module.params["resources"]
    for resource in resources:
        if 'amount' not in resource:
            continue
        amount = resource["amount"]
        if isinstance(amount, str):
            try:
                amount_int = int(amount)
                resource["amount"] = amount_int
            except ValueError:
                # this will get picked up in validate_resources
                pass

    # Validate resources list
    resources_specs = [
        {
            'field': 'resource_class',
            'type': str
        },
        {
            'field': 'traits',
            'type': list
        },
        {
            'field': 'amount',
            'type': int
        },
    ]

    validate_resources(module, resources_specs)

    # Fail if there were any exceptions when importing modules.
    if IMPORT_ERRORS:
        module.fail_json(msg="Import errors: %s" %
                             ", ".join([repr(e) for e in IMPORT_ERRORS]))

    return module


def main():
    module = get_module()

    attempts_needed = 0

    # In check mode, only perform validation of parameters
    if not module.check_mode:
        attempts_needed = wait_for_resources(module)

    # This module doesn't really change anything, it just waits for
    # something to change externally
    result = {
        "changed": False,
        "iterations": attempts_needed
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
