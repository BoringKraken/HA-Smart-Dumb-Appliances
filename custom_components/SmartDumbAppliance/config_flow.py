"""
Configuration flow for Smart Dumb Appliance integration.

This module handles the setup process when a user adds the integration through
the Home Assistant UI. It creates a form where users can configure their
appliance settings, such as power sensors, cost tracking, and service reminders.
"""

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
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT
)

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle the configuration flow for Smart Dumb Appliance.
    
    This class manages the setup process when a user adds the integration
    through the Home Assistant UI. It creates a form where users can configure
    their appliance settings.
    """

    VERSION = 1  # Version of the configuration flow

    def __init__(self):
        """Initialize the configuration flow."""
        self._errors = {}  # Store any validation errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the initial configuration step.
        
        This method creates the configuration form and processes the user's input.
        It shows a form with all the necessary fields for configuring an appliance:
        - Device name (required)
        - Power sensor (required)
        - Cost sensor (optional)
        - Dead zone (optional)
        - Debounce time (optional)
        - Service reminder settings (optional)
        """
        if user_input is not None:
            # User has submitted the form, create the configuration entry
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data=user_input
            )

        # Create the configuration form
        schema = vol.Schema({
            # Required fields
            vol.Required(CONF_DEVICE_NAME, default="My Appliance"): str,
            vol.Required(CONF_POWER_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            
            # Optional fields with defaults
            vol.Optional(CONF_COST_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["input_number", "number"])
            ),
            vol.Optional(CONF_DEAD_ZONE, default=DEFAULT_DEAD_ZONE): vol.Coerce(float),
            vol.Optional(CONF_DEBOUNCE, default=DEFAULT_DEBOUNCE): vol.Coerce(float),
            
            # Service reminder settings
            vol.Optional(CONF_SERVICE_REMINDER, default=False): bool,
            vol.Optional(CONF_SERVICE_REMINDER_COUNT, default=DEFAULT_SERVICE_REMINDER_COUNT): vol.Coerce(int),
            vol.Optional(CONF_SERVICE_REMINDER_MESSAGE, default="Time for maintenance"): str,
        })

        # Show the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors,
        )
