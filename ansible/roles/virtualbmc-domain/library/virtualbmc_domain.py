#!/usr/bin/env python3

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

from ansible.module_utils.basic import AnsibleModule # noqa

import json
import os.path
import time


DOCUMENTATION = '''
---
module: virtualbmc_domain
short_description: Manages domains in VirtualBMC.
'''


RETRIES = 60
INTERVAL = 0.5


def _vbmc_command(module, args):
    path_prefix = ("%s/bin" % module.params["virtualenv"]
                   if module.params["virtualenv"] else None)
    cmd = ["vbmc", "--no-daemon"]
    if module.params["log_directory"]:
        log_file = os.path.join(module.params["log_directory"],
                                "vbmc-%s.log" % module.params["domain"])
        cmd += ["--log-file", log_file]
    cmd += args
    result = module.run_command(cmd, check_rc=True, path_prefix=path_prefix)
    rc, out, err = result
    return out


def _get_domain(module, allow_missing=False):
    domain_name = module.params["domain"]
    if allow_missing:
        # Use a list to avoid failing if the domain does not exist.
        domains = _vbmc_command(module, ["list", "-f", "json"])
        domains = json.loads(domains)
        # vbmc list returns a list of dicts. Transform into a dict of dicts
        # keyed by domain name.
        domains = {d["Domain name"]: d for d in domains}
        try:
            return domains[domain_name]
        except KeyError:
            return None
    else:
        domain = _vbmc_command(module, ["show", domain_name, "-f", "json"])
        domain = json.loads(domain)
        domain = {field["Property"]: field["Value"] for field in domain}
        return domain


def _add_domain(module):
    domain_name = module.params["domain"]
    args = [
        "add", domain_name,
        "--address", module.params["ipmi_address"],
        "--port", str(module.params["ipmi_port"]),
        "--username", module.params["ipmi_username"],
        "--password", module.params["ipmi_password"],
    ]
    if module.params["libvirt_uri"]:
        args += ["--libvirt-uri", module.params["libvirt_uri"]]
    _vbmc_command(module, args)


def _wait_for_existence(module, exists):
    """Wait for the domain to exist or cease existing."""
    for _ in range(RETRIES):
        domain = _get_domain(module, allow_missing=True)
        if (exists and domain) or (not exists and not domain):
            return
    time.sleep(INTERVAL)
    action = "added" if exists else "deleted"
    module.fail_json(msg="Timed out waiting for domain %s to be %s" %
                     (module.params['domain'], action))


def _wait_for_status(module, status):
    """Wait for the domain to reach a particular status."""
    for _ in range(RETRIES):
        domain = _get_domain(module)
        if domain["status"] == status:
            return
        time.sleep(INTERVAL)
    module.fail_json(msg="Timed out waiting for domain %s to reach status "
                         "%s" % (module.params['domain'], status))


def _virtualbmc_domain(module):
    """Configure a VirtualBMC domain."""
    changed = False
    domain_name = module.params["domain"]

    # Even if the domain is present in VBMC, we can't guarantee that it's
    # configured correctly. It's easiest to delete and re-add it; this should
    # involve minimal downtime.
    domain = _get_domain(module, allow_missing=True)
    if domain and domain["Status"] == "running":
        if not module.check_mode:
            module.debug("Stopping domain %s" % domain_name)
            _vbmc_command(module, ["stop", domain_name])
            _wait_for_status(module, "down")
        changed = True

    if domain:
        if not module.check_mode:
            module.debug("Deleting domain %s" % domain_name)
            _vbmc_command(module, ["delete", domain_name])
            _wait_for_existence(module, False)
        changed = True

    if module.params['state'] == 'present':
        if not module.check_mode:
            module.debug("Adding domain %s" % domain_name)
            _add_domain(module)
            _wait_for_existence(module, True)

            module.debug("Starting domain %s" % domain_name)
            _vbmc_command(module, ["start", domain_name])
            _wait_for_status(module, "running")
        changed = True

    return {"changed": changed}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(type='str', required=True),
            ipmi_address=dict(type='str', required=True),
            ipmi_port=dict(type='int', required=True),
            ipmi_username=dict(type='str', required=True),
            ipmi_password=dict(type='str', required=True, no_log=True),
            libvirt_uri=dict(type='str'),
            log_directory=dict(type='str'),
            state=dict(type=str, default='present',
                       choices=['present', 'absent']),
            virtualenv=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    result = _virtualbmc_domain(module)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
