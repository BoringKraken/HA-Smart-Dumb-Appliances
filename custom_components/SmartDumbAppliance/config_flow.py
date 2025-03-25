import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Add additional configuration keys for wattage
CONF_START_WATTAGE = "start_wattage"
CONF_END_WATTAGE = "end_wattage"
CONF_SENSOR = "sensor_entity_id"

# Base schema for appliance configuration
APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required(CONF_SENSOR): str,  # Replaced with entity selector
        vol.Required(CONF_START_WATTAGE, default=10): int,  # Default for start wattage
        vol.Required(CONF_END_WATTAGE, default=5): int,  # Default for end wattage
        vol.Required("dead_zone", default=10): int,
        vol.Optional("debounce_time", default=30): int,
        vol.Required("cost_helper_entity_id"): str,
        vol.Optional("service_reminder", default=10): int,
    }
)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Dumb Appliance."""

    def __init__(self):
        """Initialize the config flow."""
        self._available_sensors = []

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manage the initial configuration for a new appliance."""
        # Populate the sensor list only once for the selection
        entity_registry = er.async_get(self.hass)
        if not self._available_sensors:
            self._available_sensors = [
                entity.entity_id for entity in entity_registry.entities.values()
                if entity.entity_id.startswith("sensor.")
            ]

        if user_input is not None:
            # Create the entry if user input is complete
            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Update the appliance schema with dynamic sensor options
        schema = APPLIANCE_SCHEMA.extend({
            vol.Required(CONF_SENSOR): vol.In(self._available_sensors),
            vol.Required(CONF_START_WATTAGE, default=10): int,
            vol.Required(CONF_END_WATTAGE, default=5): int,
        })

        # Present the configuration form to the user
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return an options flow handler for the config entry."""
        return SmartDumbApplianceOptionsFlowHandler(config_entry)

class SmartDumbApplianceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the Smart Dumb Appliance config entry."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for an existing config entry."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = APPLIANCE_SCHEMA.extend({
            vol.Required(CONF_SENSOR, default=self.config_entry.data.get(CONF_SENSOR)): vol.In(self._available_sensors),
            vol.Required(CONF_START_WATTAGE, default=self.config_entry.data.get(CONF_START_WATTAGE)): int,
            vol.Required(CONF_END_WATTAGE, default=self.config_entry.data.get(CONF_END_WATTAGE)): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
