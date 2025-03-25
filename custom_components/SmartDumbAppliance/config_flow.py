import logging  # Import logging to log messages
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN  # Import the domain constant

# Instantiate a logger for this module
_LOGGER = logging.getLogger(__name__)

# Schema for appliance configuration within the integration's setup
APPLIANCE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,  # Appliance name is required and should be a string
        vol.Required("sensor_entity_id"): str,  # The sensor entity ID to monitor
        vol.Required("dead_zone", default=10): int,  # Minimum threshold energy value for activation
        vol.Optional("debounce_time", default=30): int,  # Time in seconds to debounce state changes
        vol.Optional("cost_per_kwh", default=0.2): float,  # Cost per kilowatt-hour of energy
        vol.Optional("service_reminder", default=10): int,  # Usage count for service reminders
    }
)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Dumb Appliance."""

    # Set the version of the config flow schema
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manage the initial configuration for a new appliance."""
        if user_input is not None:
            # If user_input is provided, create a new config entry
            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Show a form for the user to input configuration details
        return self.async_show_form(step_id="user", data_schema=APPLIANCE_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return an options flow handler for the config entry."""
        return SmartDumbApplianceOptionsFlowHandler(config_entry)

class SmartDumbApplianceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the Smart Dumb Appliance config entry."""

    def __init__(self, config_entry):
        self.config_entry = config_entry  # Store the config entry object

    async def async_step_init(self, user_input=None):
        """Manage the options for an existing config entry."""
        if user_input is not None:
            # Update the configuration entry with new options
            return self.async_create_entry(title="", data=user_input)

        # Display the form for users to modify options
        return self.async_show_form(step_id="init", data_schema=APPLIANCE_SCHEMA)
