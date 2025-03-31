"""Config flow for Smart Dumb Appliance integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
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

_LOGGER = logging.getLogger(__name__)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Dumb Appliance."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
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
