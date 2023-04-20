
from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.errors import AnsibleError

# 3rd party imports
try:
    from faker import Faker
    from faker.providers import DynamicProvider
except ImportError:
    raise AnsibleError("Python faker module is required for this plugin.")

# Only used for the Faker library to generate fake device manufacturer.
# Note: This is not needed for the Ansible inventory plugin
device_manufacturer_provider = DynamicProvider(
    provider_name="device_manufacturer",
    elements=["Cisco", "HPE-Aruba", "Arista", "Dell", "Juniper", "VMware", "Palo Alto"]
)

def fetch_data(config_data):
    fake = Faker("en_US")

    # then add new provider to faker instance
    fake.add_provider(device_manufacturer_provider)

    data = []
    for _ in range(config_data.get("devices", 3)):
        vendor = fake.device_manufacturer()
        data.append(
            camel_dict_to_snake_dict(
                {
                    "NodeName": to_text(f"{ fake.hostname(0) }.{ fake.domain_name() }"),
                    "Vendor": to_text(vendor),
                    "IP": to_text(fake.ipv4_private()),
                    "NodeDescription": to_text(f"{vendor} Software, Version 16.6.7"),
                    "IsRouter": fake.boolean(chance_of_getting_true=25),
                    "MachineType": to_text(f"{vendor} network device"),
                    "SysObjectID": to_text("1.3.6.1.4.1.9.1.2066"),
                    "IOSVersion": to_text(f"1{fake.pyint(min_value=5, max_value=6)}.6.7"),
                    "Site": to_text(fake.state())
                }
            )
        )

    return data