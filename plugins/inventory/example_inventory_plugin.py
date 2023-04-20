"""
The inventory plugin fetch data from SolarWinds into an Ansible inventory.
Note: The data generated is all fake using the Python Faker module.
"""

# Python built-in imports
import re

#Ansible imports
from ansible.utils.display import Display
from ansible.module_utils.basic import to_native
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.inventory.group import to_safe_group_name

from ansible_collections.homelab.example_inv_plugin.plugins.plugins_utils.fetch_data_func import fetch_data

DOCUMENTATION = r"""
name: example_inventory_plugin
plugin_type: inventory
short_description: Returns Ansible inventory from fake generated data
description: Returns Ansible inventory from fake generated data
options:
    devices:
        description: The number of devices to generate for the inventory
        required: false
        type: int
    filter_group_name:
        description: Filter inventory to only include hosts from the specified group
        required: false
        type: List[str]
    filter_exclude_host:
        description: Filter inventory hosts to exclude any host that matches the regex pattern
        required: false
        type: List[dict]
"""

EXAMPLE = r"""
plugin: homelab.example_collection.example_inventory_plugin
strict: false
devices: 5
keyed_groups:
  - key: site | lower
    prefix: site
    separator: '_'
compose:
  custom_var: "'test custom var'"
groups:
  desktops: "inventory_hostname.startswith('desktop')"
  devices_to_update: "'15.6.7' in ios_version"
filter_group_name:
  - devices_to_update
filter_exclude_host:
  - key: ios_version
    regex: ^15[.].*
"""

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    # used internally by Ansible, it should match the file name but not required
    NAME = "homelab.example_collection.example_inventory_plugin"

    def verify_file(self, path):
        """return true/false if this is possibly a valid file for this plugin to consume """
        if super(InventoryModule, self).verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith(("inventory.yml", "inventory.yaml", "inv.yml", "inv.yaml")):
                return True
        return False

    def parse(self, inventory, loader, path, cache=False):
        # call base method to ensure properties are available for use with other helper methods
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        if path is None:
            raise AnsibleParserError("Path is not set correctly.")

        # this method will parse "common format" inventory sources and
        # update any options declared in DOCUMENTATION as needed
        config_data = self._read_config_data(path)

        fetched_data = fetch_data(config_data)

        for device in fetched_data:
            try:
                group = to_safe_group_name(device["site"], replacer="_", force=True)
                name = device["node_name"]
                del device["node_name"]
                host_vars = device
                inventory.add_group(group=group)
                inventory.add_host(host=name, group=group)
                for key, value in host_vars.items():
                    inventory.set_variable(name, key, value)
            except KeyError as error:
                print(to_native(error))

            # Composed variables
            self._set_composite_vars(config_data.get("compose"), host_vars, name,
                                    strict=config_data.get("strict", False))

            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(config_data.get("groups"), host_vars, name,
                                            strict=config_data.get("strict", False))

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(config_data.get("keyed_groups"), host_vars, name,
                                        strict=config_data.get("strict", False))

        # Filter based on the specified group name
        if config_data.get("filter_group_name"):
            for group_name in inventory.get_groups_dict():
                if group_name not in ["all", "ungrouped"]:
                    if group_name.lower() not in [
                            j.lower() for j in config_data.get("filter_group_name")
                        ]:
                        inventory.remove_group(group_name)

        if config_data.get("filter_exclude_host"):
            # Gather hosts to remove
            hosts_to_remove = [
                host
                for host in inventory.hosts.values()
                for exclude_values in config_data.get("filter_exclude_host")
                if re.match(
                    exclude_values["regex"],
                    host.vars.get(exclude_values["key"], ""),
                    flags=re.IGNORECASE,
                )
            ]
            # Remove hosts from the inventory
            for host in hosts_to_remove:
                inventory.remove_host(host)

        # Only needed if you want to clean cached, other than that
        # is not needed. I am leaving it there as an example.
        inventory.reconcile_inventory()
