import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import selector
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Constants for friendly configuration
CONF_START_WATTAGE = "start_wattage"
CONF_END_WATTAGE = "end_wattage"
CONF_SENSOR = "sensor_entity_id"

# Friendly schema reordering and adjustments
APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,  # Name of Dumb Appliance
        vol.Required(CONF_SENSOR): vol.Any(str, selector({"entity": {"domain": "sensor"}})),  # Entity selector with filtering
        vol.Required(CONF_START_WATTAGE, default=10): int,  # Start Wattage
        vol.Required(CONF_END_WATTAGE, default=5): int,  # End Wattage
        vol.Required("dead_zone", default=10): int,  # Wattage Deadzone
        vol.Optional("debounce_time", default=30): int,  # Debounce Count
        vol.Required("cost_helper_entity_id"): str,  # Cost Helper
        vol.Optional("service_reminder", default=10): int,  # Cycle Count
    }
)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Dumb Appliance."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Execute user configuration."""

        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=APPLIANCE_SCHEMA)

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

        return self.async_show_form(step_id="init", data_schema=APPLIANCE_SCHEMA)
