import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_START_WATTAGE = "start_wattage"
CONF_END_WATTAGE = "end_wattage"
CONF_SENSOR = "sensor_entity_id"

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
        _LOGGER.debug("Executing async_step_user with input: %s", user_input)

        if self._async_current_entries():
            _LOGGER.debug("Integration already configured. Aborting.")
            return self.async_abort(reason="single_instance_allowed")
        
        if user_input is not None:
            _LOGGER.debug("User input provided, creating an entry.")
            return self.async_create_entry(title=user_input["name"], data=user_input)

        _LOGGER.debug("Showing user form with appliance schema.")
        return self.async_show_form(step_id="user", data_schema=APPLIANCE_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartDumbApplianceOptionsFlowHandler(config_entry)

class SmartDumbApplianceOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        _LOGGER.debug("Initializing OptionsFlowHandler")
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        _LOGGER.debug("Options step init with user input: %s", user_input)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=APPLIANCE_SCHEMA)
