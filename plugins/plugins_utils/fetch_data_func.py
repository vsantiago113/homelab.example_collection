from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.errors import AnsibleError

try:
    from faker import Faker
    from faker.providers import DynamicProvider
except ImportError:
    raise AnsibleError("Python faker module is required for this plugin.")

device_manufacturer_provider = DynamicProvider(
    provider_name="device_manufacturer",
    elements=["Cisco", "HPE-Aruba", "Arista", "Dell", "Juniper", "VMware", "Palo Alto"]
)


def fetch_data(config_data: dict) -> list[dict]:
    """
    Generate a list of fake device data.

    Args:
        config_data (dict): Configuration data for generating devices.

    Returns:
        list[dict]: A list of dictionaries with fake device information.
    """
    fake = Faker("en_US")
    fake.add_provider(device_manufacturer_provider)

    data = []
    num_devices = config_data.get("devices", 3)

    for _ in range(num_devices):
        vendor = fake.device_manufacturer()
        device_data = {
            "node_name": to_text(f"{fake.hostname(0)}.{fake.domain_name()}"),
            "vendor": to_text(vendor),
            "ip": to_text(fake.ipv4_private()),
            "node_description": to_text(f"{vendor} Software, Version 16.6.7"),
            "is_router": fake.boolean(chance_of_getting_true=25),
            "machine_type": to_text(f"{vendor} network device"),
            "sys_object_id": to_text("1.3.6.1.4.1.9.1.2066"),
            "ios_version": to_text(f"1{fake.pyint(min_value=5, max_value=6)}.6.7"),
            "site": to_text(fake.state())
        }
        # Convert keys to snake_case
        data.append(camel_dict_to_snake_dict(device_data))

    return data
