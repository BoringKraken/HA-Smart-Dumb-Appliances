"""
Defines the Config Flow for Smart Dumb Appliance, allowing users to add/edit devices.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_DEAD_ZONE,
    CONF_DEBOUNCE,
    CONF_DEVICE_NAME,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE
)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """The main config flow for adding a new Smart Dumb Appliance device."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step where user configures the device."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(CONF_DEVICE_NAME, default="My Appliance"): str,
            vol.Required(CONF_POWER_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(CONF_COST_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["number"])
            ),
            vol.Optional(CONF_DEAD_ZONE, default=DEFAULT_DEAD_ZONE): vol.Coerce(float),
            vol.Optional(CONF_DEBOUNCE, default=DEFAULT_DEBOUNCE): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler for updating an existing entry."""
        return SmartDumbApplianceOptionsFlowHandler(config_entry)


class SmartDumbApplianceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles the 'Options' flow to edit an existing device's settings."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._errors = {}

    async def async_step_init(self, user_input=None):
        """Show or process the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_data = dict(self.config_entry.data)

        schema = vol.Schema({
            vol.Required(
                CONF_DEVICE_NAME,
                default=current_data.get(CONF_DEVICE_NAME, "My Appliance")
            ): str,
            vol.Required(
                CONF_POWER_SENSOR,
                default=current_data.get(CONF_POWER_SENSOR, "")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(
                CONF_COST_SENSOR,
                default=current_data.get(CONF_COST_SENSOR, "")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["number"])
            ),
            vol.Optional(
                CONF_DEAD_ZONE,
                default=current_data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)
            ): vol.Coerce(float),
            vol.Optional(
                CONF_DEBOUNCE,
                default=current_data.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)
            ): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=self._errors
        )
