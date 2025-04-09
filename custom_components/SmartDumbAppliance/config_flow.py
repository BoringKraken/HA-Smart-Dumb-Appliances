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
    CONF_DEBOUNCE,
    CONF_DEVICE_NAME,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT
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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle the initial configuration step.
        
        This method creates the configuration form and processes the user's input.
        It shows a form with all the necessary fields for configuring an appliance:
        - Device name (required)
        - Power sensor (required)
        - Start/Stop watt thresholds (required)
        - Cost sensor (optional)
        - Debounce time (optional)
        - Service reminder settings (optional)
        """
        if user_input is not None:
            # Validate the input
            self._errors = validate_watt_thresholds(user_input)
            
            if not self._errors:
                # User has submitted the form, create the configuration entry
                return self.async_create_entry(
                    title=user_input[CONF_DEVICE_NAME],
                    data=user_input
                )

        # Create the configuration form
        schema = vol.Schema({
            # Required fields
            vol.Required(
                CONF_DEVICE_NAME,
                default="My Appliance",
                description={"suffix": "Name shown in Home Assistant"}
            ): str,
            vol.Required(
                CONF_POWER_SENSOR,
                description={"suffix": "Sensor that measures power in watts"}
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(
                CONF_START_WATTS,
                default=DEFAULT_START_WATTS,
                description={
                    "suffix": " watts",
                    "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts."
                }
            ): vol.Coerce(float),
            vol.Required(
                CONF_STOP_WATTS,
                default=DEFAULT_STOP_WATTS,
                description={
                    "suffix": " watts",
                    "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts."
                }
            ): vol.Coerce(float),
            
            # Optional fields with defaults
            vol.Optional(
                CONF_COST_SENSOR,
                description={"suffix": "Sensor providing cost per kWh"}
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["input_number", "number"])
            ),
            vol.Optional(
                CONF_DEBOUNCE,
                default=DEFAULT_DEBOUNCE,
                description={
                    "suffix": " seconds",
                    "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling."
                }
            ): vol.Coerce(float),
            
            # Service reminder settings
            vol.Optional(
                CONF_SERVICE_REMINDER,
                default=False,
                description={"tooltip": "Enable service reminders after a set number of uses"}
            ): bool,
            vol.Optional(
                CONF_SERVICE_REMINDER_COUNT,
                default=DEFAULT_SERVICE_REMINDER_COUNT,
                description={"tooltip": "Number of uses before showing a service reminder"}
            ): vol.Coerce(int),
            vol.Optional(
                CONF_SERVICE_REMINDER_MESSAGE,
                default="Time for maintenance",
                description={"tooltip": "Message to show when service is needed"}
            ): str,
        })

        # Show the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Handle reconfiguration of an existing entry.
        
        This method allows users to modify the settings of an existing
        appliance configuration.
        """
        # Get the current configuration from the context
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            _LOGGER.error("Failed to find entry for reconfiguration")
            return self.async_abort(reason="no_entry")
            
        # Try to get current values from the energy usage sensor
        current_config = entry.data
        energy_sensor_id = f"sensor.{entry.data[CONF_DEVICE_NAME].lower().replace(' ', '_')}_energy_usage"
        energy_sensor = self.hass.states.get(energy_sensor_id)
        
        if energy_sensor and energy_sensor.attributes:
            # Use values from sensor attributes if available
            current_config = {
                **current_config,  # Keep any values not in attributes
                CONF_START_WATTS: energy_sensor.attributes.get("start_watts", current_config.get(CONF_START_WATTS, DEFAULT_START_WATTS)),
                CONF_STOP_WATTS: energy_sensor.attributes.get("stop_watts", current_config.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)),
                CONF_DEBOUNCE: energy_sensor.attributes.get("debounce", current_config.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)),
                CONF_POWER_SENSOR: energy_sensor.attributes.get("power_sensor", current_config.get(CONF_POWER_SENSOR)),
                CONF_COST_SENSOR: energy_sensor.attributes.get("cost_sensor", current_config.get(CONF_COST_SENSOR)),
                CONF_SERVICE_REMINDER: energy_sensor.attributes.get("service_reminder_enabled", current_config.get(CONF_SERVICE_REMINDER, False)),
                CONF_SERVICE_REMINDER_COUNT: energy_sensor.attributes.get("service_reminder_count", current_config.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)),
                CONF_SERVICE_REMINDER_MESSAGE: energy_sensor.attributes.get("service_reminder_message", current_config.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance")),
            }

        # If user input is provided, update the configuration
        if user_input is not None:
            # Validate the watt thresholds
            threshold_errors = validate_watt_thresholds(user_input)
            if threshold_errors:
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=vol.Schema({
                        vol.Required(
                            CONF_DEVICE_NAME,
                            default=user_input.get(CONF_DEVICE_NAME, current_config.get(CONF_DEVICE_NAME)),
                            description={"suffix": "Name shown in Home Assistant"}
                        ): str,
                        vol.Required(
                            CONF_POWER_SENSOR,
                            default=user_input.get(CONF_POWER_SENSOR, current_config.get(CONF_POWER_SENSOR)),
                            description={"suffix": "Sensor that measures power in watts"}
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=["sensor"])
                        ),
                        vol.Required(
                            CONF_START_WATTS,
                            default=user_input.get(CONF_START_WATTS, current_config.get(CONF_START_WATTS, DEFAULT_START_WATTS)),
                            description={
                                "suffix": " watts",
                                "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts."
                            }
                        ): vol.Coerce(float),
                        vol.Required(
                            CONF_STOP_WATTS,
                            default=user_input.get(CONF_STOP_WATTS, current_config.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)),
                            description={
                                "suffix": " watts",
                                "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts."
                            }
                        ): vol.Coerce(float),
                        vol.Optional(
                            CONF_COST_SENSOR,
                            default=user_input.get(CONF_COST_SENSOR, current_config.get(CONF_COST_SENSOR)),
                            description={"suffix": "Sensor providing cost per kWh"}
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=["input_number", "number"])
                        ),
                        vol.Optional(
                            CONF_DEBOUNCE,
                            default=user_input.get(CONF_DEBOUNCE, current_config.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)),
                            description={
                                "suffix": " seconds",
                                "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling."
                            }
                        ): vol.Coerce(float),
                        vol.Optional(
                            CONF_SERVICE_REMINDER,
                            default=user_input.get(CONF_SERVICE_REMINDER, current_config.get(CONF_SERVICE_REMINDER, False)),
                            description={"tooltip": "Enable service reminders after a set number of uses"}
                        ): bool,
                        vol.Optional(
                            CONF_SERVICE_REMINDER_COUNT,
                            default=user_input.get(CONF_SERVICE_REMINDER_COUNT, current_config.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)),
                            description={"tooltip": "Number of uses before showing a service reminder"}
                        ): vol.Coerce(int),
                        vol.Optional(
                            CONF_SERVICE_REMINDER_MESSAGE,
                            default=user_input.get(CONF_SERVICE_REMINDER_MESSAGE, current_config.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance")),
                            description={"tooltip": "Message to show when service is needed"}
                        ): str,
                    }),
                    errors=threshold_errors,
                )

            # Update the configuration entry
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
                reason="reconfigure_successful"
            )

        # Show the reconfiguration form with current values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_DEVICE_NAME,
                    default=current_config.get(CONF_DEVICE_NAME),
                    description={"suffix": "Name shown in Home Assistant"}
                ): str,
                vol.Required(
                    CONF_POWER_SENSOR,
                    default=current_config.get(CONF_POWER_SENSOR),
                    description={"suffix": "Sensor that measures power in watts"}
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_START_WATTS,
                    default=current_config.get(CONF_START_WATTS, DEFAULT_START_WATTS),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts."
                    }
                ): vol.Coerce(float),
                vol.Required(
                    CONF_STOP_WATTS,
                    default=current_config.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts."
                    }
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_COST_SENSOR,
                    default=current_config.get(CONF_COST_SENSOR),
                    description={"suffix": "Sensor providing cost per kWh"}
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["input_number", "number"])
                ),
                vol.Optional(
                    CONF_DEBOUNCE,
                    default=current_config.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE),
                    description={
                        "suffix": " seconds",
                        "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling."
                    }
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_SERVICE_REMINDER,
                    default=current_config.get(CONF_SERVICE_REMINDER, False),
                    description={"tooltip": "Enable service reminders after a set number of uses"}
                ): bool,
                vol.Optional(
                    CONF_SERVICE_REMINDER_COUNT,
                    default=current_config.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT),
                    description={"tooltip": "Number of uses before showing a service reminder"}
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_SERVICE_REMINDER_MESSAGE,
                    default=current_config.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance"),
                    description={"tooltip": "Message to show when service is needed"}
                ): str,
            }),
            errors=self._errors,
        )
