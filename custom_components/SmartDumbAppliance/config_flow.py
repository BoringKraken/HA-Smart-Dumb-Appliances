import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import ENERGY_KILO_WATT_HOUR, POWER_WATT
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_registry import async_get_registry
from homeassistant.helpers.selector import selector
from homeassistant.util import Throttle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Configuration constants for user inputs
CONF_START_WATTAGE = "start_wattage"
CONF_END_WATTAGE = "end_wattage"
CONF_SENSOR = "sensor_entity_id"

# Define schema for configuring an appliance
APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required(CONF_SENSOR): vol.Any(str, selector({"entity": {"domain": "sensor"}})),
        vol.Required(CONF_START_WATTAGE, default=10): int,
        vol.Required(CONF_END_WATTAGE, default=5): int,
        vol.Required("dead_zone", default=10): int,
        vol.Optional("debounce_time", default=30): int,
        vol.Required("cost_helper_entity_id"): str,
        vol.Optional("service_reminder", default=10): int,
    }
)

@config_entries.HANDLERS.register(DOMAIN)
class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user initiated flow."""
        errors = {}

        if user_input is not None:
            # Proceed with the user input to create entities
            await self._create_entities(user_input)
            return self.async_create_entry(title=user_input["name"], data=user_input)
        
        return self.async_show_form(
            step_id="user", data_schema=APPLIANCE_SCHEMA, errors=errors
        )

    async def _create_entities(self, config):
        """Create entities for the newly added appliance."""
        name = config.get("name")

        # Retrieve entity registry
        registry = await async_get_registry(self.hass)

        # Create a status entity
        registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=f"{name}_status",
            name=f"{name} Status",
            unit_of_measurement=None,
            device_class=None,
            suggested_entity_id=f"sensor.{name.lower()}_status",
        )

        # Create a daily electricity consumption entity
        registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=f"{name}_power_used_today",
            name=f"{name} Power Used Today",
            unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class="energy",
            suggested_entity_id=f"sensor.{name.lower()}_power_today",
        )

        # Create a monthly electricity consumption entity
        registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=f"{name}_power_used_month",
            name=f"{name} Power Used This Month",
            unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class="energy",
            suggested_entity_id=f"sensor.{name.lower()}_power_month",
        )

        # Create a cycles till service entity
        registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=f"{name}_cycles_remaining",
            name=f"{name} Cycles Remaining",
            suggested_entity_id=f"sensor.{name.lower()}_cycles_remaining",
        )

        # Create entities for user input values (for display)
        for key in [CONF_START_WATTAGE, CONF_END_WATTAGE, "service_reminder"]:
            registry.async_get_or_create(
                domain="sensor",
                platform=DOMAIN,
                unique_id=f"{name}_{key}",
                name=f"{name} {key.replace('_', ' ').title()}",
                unit_of_measurement=POWER_WATT if "wattage" in key else None,
                device_class=None,
                suggested_entity_id=f"sensor.{name.lower()}_{key}",
            )

        # Optionally add more entities for additional user inputs like debounce count