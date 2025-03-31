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
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEAD_ZONE,
    CONF_DEBOUNCE,
    CONF_DEVICE_NAME,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT,
    DEFAULT_CONFIG,
)

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

def validate_watt_thresholds(data: dict[str, Any]) -> dict[str, str]:
    """
    Validate that watt thresholds are in the correct order.
    
    Args:
        data: The configuration data to validate
        
    Returns:
        dict: Any validation errors found
    """
    errors = {}
    
    # Check that stop watts is less than start watts
    if data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS) >= data.get(CONF_START_WATTS, DEFAULT_START_WATTS):
        errors[CONF_STOP_WATTS] = "Stop watts must be less than start watts"
    
    # Check that dead zone is less than stop watts
    if data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE) >= data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS):
        errors[CONF_DEAD_ZONE] = "Dead zone must be less than stop watts"
    
    return errors

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
        self._show_advanced = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the initial step of the configuration flow.
        
        Args:
            user_input: The user's input data
            
        Returns:
            FlowResult: The flow result
        """
        errors = {}

        if user_input is not None:
            # If user toggled advanced options, show them
            if "show_advanced" in user_input:
                self._show_advanced = user_input["show_advanced"]
                return await self.async_step_user(None)
            
            # Validate the watt thresholds
            threshold_errors = validate_watt_thresholds(user_input)
            if threshold_errors:
                errors["base"] = threshold_errors[0]  # Show first error
            else:
                # Create the configuration entry
                return self.async_create_entry(
                    title=user_input["device_name"],
                    data=user_input,
                )

        # Get all power sensors
        power_sensors = get_power_sensors(self.hass)

        # If no power sensors found, show error
        if not power_sensors:
            return self.async_abort(
                reason="no_power_sensors",
                description_placeholders={
                    "docs_url": "https://github.com/BoringKraken/HA-Smart-Dumb-Appliances"
                },
            )

        # Create the schema with the found power sensors
        schema = {
            vol.Required(
                "device_name",
                default=user_input.get("device_name") if user_input else None,
                description={
                    "tooltip": "Enter a name for this appliance. This will be used to identify it in Home Assistant and for all related entities."
                }
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                    autocomplete="off",
                )
            ),
            vol.Required(
                CONF_POWER_SENSOR,
                default=user_input.get(CONF_POWER_SENSOR) if user_input else None,
                description={
                    "suffix": " watts",
                    "tooltip": "Select any sensor that measures power consumption. The integration will work with any numerical sensor that reports power values."
                }
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    entity_category=None,
                    include_entities=power_sensors,
                    multiple=False,
                )
            ),
            vol.Optional(
                "show_advanced",
                default=self._show_advanced,
                description={
                    "tooltip": "Show advanced configuration options"
                }
            ): selector.BooleanSelector(
                selector.BooleanSelectorConfig()
            ),
        }

        # Add advanced options if enabled
        if self._show_advanced:
            schema.update({
                vol.Optional(
                    CONF_START_WATTS,
                    default=user_input.get(CONF_START_WATTS, DEFAULT_CONFIG[CONF_START_WATTS]),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts. When power exceeds this value, the appliance is considered 'on'."
                    }
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_STOP_WATTS,
                    default=user_input.get(CONF_STOP_WATTS, DEFAULT_CONFIG[CONF_STOP_WATTS]),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts. When power drops below this value, the appliance is considered 'off'."
                    }
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEAD_ZONE,
                    default=user_input.get(CONF_DEAD_ZONE, DEFAULT_CONFIG[CONF_DEAD_ZONE]),
                    description={
                        "suffix": " watts",
                        "tooltip": "Minimum power threshold to consider appliance as 'on'. Must be lower than stop watts. Prevents false readings from standby power."
                    }
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEBOUNCE,
                    default=user_input.get(CONF_DEBOUNCE, DEFAULT_CONFIG[CONF_DEBOUNCE]),
                    description={
                        "suffix": " seconds",
                        "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling from power fluctuations. Higher values make the detection more stable but less responsive."
                    }
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="seconds",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER,
                    default=user_input.get(CONF_SERVICE_REMINDER, DEFAULT_CONFIG[CONF_SERVICE_REMINDER]),
                    description={
                        "tooltip": "Enable service reminders to track appliance usage and notify you when maintenance is needed. When enabled, you can set the number of uses before a reminder."
                    }
                ): selector.BooleanSelector(
                    selector.BooleanSelectorConfig()
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_COUNT,
                    default=user_input.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_CONFIG[CONF_SERVICE_REMINDER_COUNT]),
                    description={
                        "tooltip": "Number of times the appliance can be used before showing a service reminder. Only applies if service reminders are enabled."
                    }
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=1000,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_MESSAGE,
                    default=user_input.get(CONF_SERVICE_REMINDER_MESSAGE, DEFAULT_CONFIG[CONF_SERVICE_REMINDER_MESSAGE]),
                    description={
                        "tooltip": "Custom message to show when service is needed. If left empty, a default message will be used. The message will reset after the next use."
                    }
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                        autocomplete="off",
                    )
                ),
            })

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle reconfiguration of an existing entry.
        
        This method allows users to modify the settings of an existing
        appliance configuration.
        """
        return await self.async_step_user(user_input)
