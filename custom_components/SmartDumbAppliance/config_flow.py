import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema for appliance configuration within the integration's setup
APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,  # Appliance name is required and should be a string
        vol.Required("sensor_entity_id"): str,  # The sensor providing power data
        vol.Required("dead_zone", default=10): int,  # Threshold energy below which appliance is off
        vol.Optional("debounce_time", default=30): int,  # Time in seconds to debounce state changes
        vol.Required("cost_helper_entity_id"): str,  # New: entity ID for cost per kWh
        vol.Optional("service_reminder", default=10): int,  # Use count for service reminders
    }
)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Dumb Appliance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manage the initial configuration for a new appliance."""
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Show a form for user input on configuration details
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

        # Display the form for users to modify options
        return self.async_show_form(step_id="init", data_schema=APPLIANCE_SCHEMA)
