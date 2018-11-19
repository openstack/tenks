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

from __future__ import absolute_import
import copy
import imp
import json
import os
import random
from itertools import repeat, chain, cycle

from ansible.module_utils import basic

from tests.utils import ModuleTestCase, set_module_args, AnsibleExitJson, \
    AnsibleFailJson

# Python 2/3 compatibility.
try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch  # noqa

# Import method lifted from kolla_ansible's test_merge_config.py
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
PLUGIN_FILE = os.path.join(PROJECT_DIR,
                           'ansible/roles/wait-for-resources/library'
                           '/wait_for_resources.py')

wait_for = imp.load_source('wait_for_resources', PLUGIN_FILE)

meets_criteria = wait_for.meets_criteria
get_providers = wait_for.get_providers
get_inventory = wait_for.get_inventory
get_traits = wait_for.get_traits
merge = wait_for.merge
get_openstack_binary_path = wait_for.get_openstack_binary_path
Specifier = wait_for.Specifier

inventory_list_out = """[
  {
    "allocation_ratio": 1.0, 
    "total": 1, 
    "reserved": 0, 
    "resource_class": "CUSTOM_TEST_RC", 
    "step_size": 1, 
    "min_unit": 1, 
    "max_unit": 1
  }
]"""  # noqa

inventory_custom_b_out = """[
  {
    "allocation_ratio": 1.0, 
    "total": 1, 
    "reserved": 0, 
    "resource_class": "CUSTOM_B", 
    "step_size": 1, 
    "min_unit": 1, 
    "max_unit": 1
  }
]"""  # noqa

inventory_reserved_out = """[
  {
    "allocation_ratio": 1.0, 
    "total": 1, 
    "reserved": 1, 
    "resource_class": "CUSTOM_TEST_RC", 
    "step_size": 1, 
    "min_unit": 1, 
    "max_unit": 1
  }
]""" # noqa

inventory_list = [{'allocation_ratio': 1.0,
                   'max_unit': 1,
                   'min_unit': 1,
                   'reserved': 0,
                   'resource_class': 'CUSTOM_TEST_RC',
                   'step_size': 1,
                   'total': 1}]

resource_provider_list_out = """[
  {
    "generation": 2, 
    "uuid": "657c4ab0-de82-4def-b7b0-d13ce672bfd0", 
    "name": "kayobe-will-master"
  }, 
  {
    "generation": 1, 
    "uuid": "e2e78f98-d3ec-466a-862b-42d7ef5dca7d", 
    "name": "e2e78f98-d3ec-466a-862b-42d7ef5dca7d"
  }, 
  {
    "generation": 1, 
    "uuid": "07072aea-cc2b-4135-a7e2-3a4dd3a9f629", 
    "name": "07072aea-cc2b-4135-a7e2-3a4dd3a9f629"
  }
]""" # noqa

resource_provider_list = [{'generation': 2, 'name': 'kayobe-will-master',
                           'uuid': '657c4ab0-de82-4def-b7b0-d13ce672bfd0'},
                          {'generation': 1,
                           'name': 'e2e78f98-d3ec-466a-862b-42d7ef5dca7d',
                           'uuid': 'e2e78f98-d3ec-466a-862b-42d7ef5dca7d'},
                          {'generation': 1,
                           'name': '07072aea-cc2b-4135-a7e2-3a4dd3a9f629',
                           'uuid': '07072aea-cc2b-4135-a7e2-3a4dd3a9f629'}]

resource_provider_traits_out = """[
  {
    "name": "HW_CPU_X86_SSE2"
  }, 
  {
    "name": "HW_CPU_X86_CLMUL"
  }, 
  {
    "name": "HW_CPU_X86_SSE"
  }, 
  {
    "name": "HW_CPU_X86_ABM"
  }, 
  {
    "name": "HW_CPU_X86_MMX"
  }, 
  {
    "name": "HW_CPU_X86_AVX2"
  }, 
  {
    "name": "HW_CPU_X86_SSE41"
  }, 
  {
    "name": "HW_CPU_X86_SSE42"
  }, 
  {
    "name": "HW_CPU_X86_AESNI"
  }, 
  {
    "name": "HW_CPU_X86_AVX"
  }, 
  {
    "name": "HW_CPU_X86_VMX"
  }, 
  {
    "name": "HW_CPU_X86_BMI2"
  }, 
  {
    "name": "HW_CPU_X86_FMA3"
  }, 
  {
    "name": "HW_CPU_X86_SSSE3"
  }, 
  {
    "name": "HW_CPU_X86_F16C"
  }, 
  {
    "name": "HW_CPU_X86_BMI"
  }
]"""  # noqa


resource_provider_no_traits_out = """[]
"""

resource_provider_traits = {'HW_CPU_X86_SSE2',
                            'HW_CPU_X86_CLMUL',
                            'HW_CPU_X86_SSE',
                            'HW_CPU_X86_ABM',
                            'HW_CPU_X86_MMX',
                            'HW_CPU_X86_AVX2',
                            'HW_CPU_X86_SSE41',
                            'HW_CPU_X86_SSE42',
                            'HW_CPU_X86_AESNI',
                            'HW_CPU_X86_AVX',
                            'HW_CPU_X86_VMX',
                            'HW_CPU_X86_BMI2',
                            'HW_CPU_X86_FMA3',
                            'HW_CPU_X86_SSSE3',
                            'HW_CPU_X86_F16C',
                            'HW_CPU_X86_BMI'}


def traits_to_json(traits):
    return json.dumps(
        [{'name': x} for x in traits]
    )


def traits(*args):
    # converts list to frozenset
    return frozenset(*args)


resources_expected = {
    Specifier('CUSTOM_B', traits()): 2,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 3
}

resources_not_enough = {
    Specifier('CUSTOM_B', traits()): 1,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 2
}

resources_one_ok = {
    Specifier('CUSTOM_B', traits()): 2,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 2
}

resources_both_ok = {
    Specifier('CUSTOM_B', traits()): 2,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 3
}

resources_too_many = {
    Specifier('CUSTOM_B', traits()): 5,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 6
}

resources_extra_keys = {
    Specifier('CUSTOM_B', traits()): 2,
    Specifier('CUSTOM_A', traits('TRAIT_A')): 3,
    Specifier('CUSTOM_C', traits('TRAIT_A')): 3,
}

resources_key_missing = {
    'CUSTOM_B': 2
}

dummy_resources = [
    {
        "resource_class": "CUSTOM_TEST_RC",
        "traits": [],
        "amount": 3
    },
]

# Scenario definitions - we define these outside the test as we want to pass
# them into the 'patch' decorator

# scenario - resource class is incorrect on first iteration

inventory_resource_class_incorrect = chain(
    repeat(inventory_custom_b_out, 3),
    repeat(inventory_list_out, 3)
)

# scenario - resource class is reserved on first iteration

inventory_resource_class_reserved = chain(
    repeat(inventory_reserved_out, 3),
    repeat(inventory_list_out, 3)
)

# scenario - same resource class, different traits - success

# Arbitrary subset
resource_provider_traits_subset = random.sample(resource_provider_traits, 3)

resource_provider_traits_subset_out = traits_to_json(
    resource_provider_traits_subset
)

inventory_same_resource_different_traits = chain(
    # We are using a provider output with 3 providers, so we need three
    # inventory strings - one for each
    repeat(inventory_reserved_out, 1), repeat(inventory_list_out, 2)
)

traits_same_resource_different_traits = chain(
    # We are using a provider output with 3 providers, so we need three
    # trait strings - one for each
    repeat(resource_provider_no_traits_out, 1),
    repeat(resource_provider_traits_out, 1),
    repeat(resource_provider_traits_subset_out, 1)
)


def get_traits_mocked(start=0, stop=None):
    def mocked_function(_module, _provider):
        all_traits = list(resource_provider_traits)
        stop_ = stop if stop else len(all_traits)
        return frozenset(all_traits[start:stop_])
    return mocked_function


def get_dummy_resources(resource_class="CUSTOM_TEST_RC", amount=3,
                        traits=[]):
    result = [
        {
            "resource_class": resource_class,
            "traits": traits,
            "amount": amount
        },
    ]
    return result


def get_dummy_module_args(resources,
                          maximum_retries=10,
                          delay=10,
                          venv="/my/dummy/venv"):
    result = {
        'resources': resources,
        'maximum_retries': maximum_retries,
        'delay': delay,
        'venv': venv
    }
    return result


def pop_output(a):
    next_ = next(a, None)
    if next_:
        return 0, next_, ""
    else:
        return 1, "", "Ran out of input"


def noop(*_args, **_kwargs):
    pass


def create_run_cmd(providers, inventories, traits):
    def dummy_run_command(*args, **_kwargs):
        print(args)
        if "resource provider list" in args[1]:
            return pop_output(providers)
        elif "resource provider trait list" in args[1]:
            return pop_output(traits)
        elif "resource provider inventory list" in args[1]:
            return pop_output(inventories)
        else:
            raise ValueError("{} not expected", args)

    return dummy_run_command


class TestTenksWaitForResource(ModuleTestCase):

    def setUp(self):
        super(TestTenksWaitForResource, self).setUp()

    def test_meets_criteria_not_enough(self):
        self.assertFalse(meets_criteria(actual=resources_not_enough,
                                        requested=resources_expected))

    def test_meets_criteria_one_ok(self):
        self.assertFalse(meets_criteria(actual=resources_one_ok,
                                        requested=resources_expected))

    def test_meets_criteria_both_ok(self):
        self.assertTrue(meets_criteria(actual=resources_both_ok,
                                       requested=resources_expected))

    def test_meets_criteria_too_many(self):
        self.assertTrue(meets_criteria(actual=resources_too_many,
                                       requested=resources_expected))

    def test_meets_criteria_keys_we_dont_care_about(self):
        self.assertTrue(meets_criteria(actual=resources_extra_keys,
                                       requested=resources_expected))

    def test_meets_criteria_missing_key(self):
        self.assertFalse(meets_criteria(actual=resources_key_missing,
                                        requested=resources_expected))

    @patch.object(basic.AnsibleModule, 'run_command')
    def test_resource_provider_list(self, run_command):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        run_command.return_value = 0, resource_provider_list_out, ''
        set_module_args(dummy_module_arguments)
        module = wait_for.get_module()
        providers = get_providers(module)
        calls = [call for call in run_command.call_args_list if
                 "openstack resource provider list" in call[0][0]]
        self.assertGreater(len(calls), 0)
        self.assertListEqual(resource_provider_list, providers)

    @patch.object(basic.AnsibleModule, 'run_command')
    def test_inventory_list(self, run_command):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        run_command.return_value = 0, inventory_list_out, ''
        set_module_args(dummy_module_arguments)
        module = wait_for.get_module()
        expected = get_inventory(module, "provider-uuid")
        calls = [call for call in run_command.call_args_list if
                 "openstack resource provider inventory list" in call[0][0]]
        self.assertGreater(len(calls), 0)
        self.assertListEqual(expected, inventory_list)

    @patch.object(basic.AnsibleModule, 'run_command')
    def test_traits(self, run_command):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        run_command.return_value = 0, resource_provider_traits_out, ''
        set_module_args(dummy_module_arguments)
        module = wait_for.get_module()
        expected = get_traits(module, "provider-uuid")
        calls = [call for call in run_command.call_args_list if
                 "openstack resource provider trait list" in call[0][0]]
        self.assertGreater(len(calls), 0)
        self.assertSetEqual(expected, resource_provider_traits)

    def test_venv_path(self):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        module = wait_for.get_module()
        openstack_binary_path = get_openstack_binary_path(module)
        venv = dummy_module_arguments["venv"]
        expected = os.path.join(venv, "bin", "openstack")
        self.assertEqual(expected, openstack_binary_path)

    def test_venv_path_unset(self):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        args = copy.copy(dummy_module_arguments)
        del args["venv"]
        set_module_args(args)
        module = wait_for.get_module()
        openstack_binary_path = get_openstack_binary_path(module)
        expected = "openstack"
        self.assertEqual(expected, openstack_binary_path)

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=cycle(repeat(resource_provider_list_out, 1)),
                      inventories=cycle(repeat(inventory_reserved_out, 1)),
                      traits=cycle(repeat(resource_provider_no_traits_out, 3))
                  ))
    @patch('time.sleep', noop)
    def test_main_failure_exhaust_retries(self):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        expected_msg = wait_for._RETRY_LIMIT_FAILURE_TEMPLATE.format(
            max_retries=dummy_module_arguments["maximum_retries"])
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=cycle(repeat(resource_provider_list_out, 1)),
                      inventories=cycle(repeat(inventory_list_out, 1)),
                      traits=cycle(repeat(resource_provider_traits_out, 3))
                  ))
    @patch('time.sleep', noop)
    @patch.object(wait_for, 'get_traits', get_traits_mocked(0, 2))
    def test_main_failure_provider_does_not_provide_all_traits(
            self):
        expected_traits = list(resource_provider_traits)
        resources = get_dummy_resources(traits=expected_traits)
        dummy_module_arguments = get_dummy_module_args(
            resources=resources,
        )
        set_module_args(dummy_module_arguments)
        expected_msg = wait_for._RETRY_LIMIT_FAILURE_TEMPLATE.format(
            max_retries=dummy_module_arguments["maximum_retries"])
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=cycle(repeat(resource_provider_list_out, 1)),
                      inventories=cycle(repeat(inventory_list_out, 1)),
                      traits=cycle(repeat(resource_provider_traits_out, 3))
                  ))
    @patch('time.sleep', noop)
    def test_main_failure_request_subset_of_traits(
            self):
        # pick an arbitrary sub range of traits
        expected_traits = list(resource_provider_traits)[3:6]
        resources = get_dummy_resources(traits=expected_traits)
        dummy_module_arguments = get_dummy_module_args(
            resources=resources,
        )
        set_module_args(dummy_module_arguments)
        expected_msg = wait_for._RETRY_LIMIT_FAILURE_TEMPLATE.format(
            max_retries=dummy_module_arguments["maximum_retries"])
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=cycle(repeat(resource_provider_list_out, 1)),
                      inventories=cycle(repeat(inventory_reserved_out, 1)),
                      traits=cycle(repeat(resource_provider_no_traits_out, 3))
                  ))
    @patch('time.sleep', noop)
    def test_main_failure_exhaust_retries_traits_not_matched(self):
        resources = get_dummy_resources(traits=["WE_NEED_THIS"])
        dummy_module_arguments = get_dummy_module_args(
            resources=resources
        )
        set_module_args(dummy_module_arguments)
        expected_msg = wait_for._RETRY_LIMIT_FAILURE_TEMPLATE.format(
            max_retries=dummy_module_arguments["maximum_retries"])
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 1),
                      # one per provider
                      inventories=repeat(inventory_list_out, 3),
                      traits=repeat(resource_provider_no_traits_out, 3)
                  ))
    def test_main_success_one_iteration(self):
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        with self.assertRaises(AnsibleExitJson) as cm:
            wait_for.main()
        exception = cm.exception
        self.assertFalse(exception.args[0]['changed'])
        self.assertEqual(1, exception.args[0]["iterations"])

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 1),
                      inventories=inventory_same_resource_different_traits,
                      traits=traits_same_resource_different_traits
                  ))
    def test_main_success_same_resource_class_different_traits(self):
        resource_a = get_dummy_resources(
            traits=list(resource_provider_traits_subset),
            amount=1
        )
        resource_b = get_dummy_resources(
            traits=list(resource_provider_traits),
            amount=1
        )
        dummy_module_arguments = get_dummy_module_args(
            resources=resource_a + resource_b,
        )
        set_module_args(dummy_module_arguments)
        try:
            wait_for.main()
        except AnsibleExitJson as result:
            self.assertFalse(result.args[0]['changed'])
            self.assertEqual(1, result.args[0]["iterations"])
        else:
            self.fail("Should have thrown AnsibleExitJson")

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 1),
                      # one per provider
                      inventories=repeat(inventory_list_out, 3),
                      traits=repeat(resource_provider_no_traits_out, 3)
                  ))
    def test_main_success_no_traits(self):
        # if the resource provider doesn't have any traits and no traits
        # were requested, this should still pass
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        try:
            wait_for.main()
        except AnsibleExitJson as result:
            self.assertFalse(result.args[0]['changed'])
            self.assertEqual(1, result.args[0]["iterations"])
        else:
            self.fail("Should have thrown AnsibleExitJson")

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 2),
                      # one per provider * 2 iterations
                      inventories=inventory_resource_class_incorrect,
                      traits=repeat(resource_provider_no_traits_out, 6)))
    @patch('time.sleep', noop)
    def test_success_first_iteration_wrong_resource_class(self):
        # different resource class to the one we are looking for on first
        # iteration
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        try:
            wait_for.main()
        except AnsibleExitJson as result:
            self.assertFalse(result.args[0]['changed'])
            self.assertEqual(2, result.args[0]["iterations"])
        else:
            self.fail("Should have thrown AnsibleExitJson")

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 2),
                      inventories=inventory_resource_class_reserved,
                      # one per provider * 2 iterations
                      traits=repeat(resource_provider_no_traits_out, 6)))
    @patch('time.sleep', noop)
    def test_success_resource_class_reserved(self):
        # resource class is reserved on the first iteration
        dummy_module_arguments = get_dummy_module_args(
            resources=dummy_resources
        )
        set_module_args(dummy_module_arguments)
        try:
            wait_for.main()
        except AnsibleExitJson as result:
            self.assertFalse(result.args[0]['changed'])
            self.assertEqual(2, result.args[0]["iterations"])
        else:
            self.fail("Should have thrown AnsibleExitJson")

    @patch.object(basic.AnsibleModule, 'run_command',
                  create_run_cmd(
                      providers=repeat(resource_provider_list_out, 1),
                      # one per provider
                      inventories=repeat(inventory_list_out, 3),
                      traits=repeat(resource_provider_no_traits_out, 3)
                  ))
    def test_validation_amount_is_str_repr_of_int(self):
        dummy_module_arguments = get_dummy_module_args(
            # amount should be an int
            resources=get_dummy_resources(amount="3")
        )
        set_module_args(dummy_module_arguments)
        try:
            wait_for.main()
        except AnsibleExitJson as result:
            self.assertFalse(result.args[0]['changed'])
            self.assertEqual(1, result.args[0]["iterations"])
        else:
            self.fail("Should have thrown AnsibleExitJson")

    def test_validation_amount_not_int(self):
        dummy_module_arguments = get_dummy_module_args(
            # amount should be an int
            resources=get_dummy_resources(amount="not_a_number")
        )
        set_module_args(dummy_module_arguments)
        expected_msg = "amount, should be type int"
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    def test_validation_amount_missing(self):
        resources = get_dummy_resources()
        for resource in resources:
            del resource["amount"]
        dummy_module_arguments = get_dummy_module_args(
            resources=resources
        )
        set_module_args(dummy_module_arguments)
        expected_msg = (
            "One of your resources does not have the field, amount, set"
        )
        self.assertRaisesRegex(AnsibleFailJson, expected_msg, wait_for.main)

    def test_merge_simple(self):
        a = {'a': 1, 'b': 2}
        b = {'a': 3, 'c': 5}
        expected = {'a': 4, 'b': 2, 'c': 5}
        merged = merge(a, b, lambda x, y: x + y)
        self.assertDictEqual(expected, merged)
