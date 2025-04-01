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
        entry = self.context.get("entry")
        if not entry:
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
                            "device_name",
                            default=user_input.get("device_name", current_config.get("device_name")),
                            description={
                                "tooltip": "Enter a name for this appliance. This will be used to identify it in Home Assistant and for all related entities."
                            }
                        ): str,
                        vol.Required(
                            CONF_POWER_SENSOR,
                            default=user_input.get(CONF_POWER_SENSOR, current_config.get(CONF_POWER_SENSOR)),
                            description={
                                "suffix": " watts",
                                "tooltip": "Select any sensor that measures power consumption. The integration will work with any numerical sensor that reports power values."
                            }
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                entity_category=None,
                                domain=["sensor"],
                                multiple=False,
                            )
                        ),
                        vol.Optional(
                            "show_advanced",
                            default=self._show_advanced,
                            description={
                                "tooltip": "Show advanced configuration options"
                            }
                        ): bool,
                    }),
                    errors={"base": threshold_errors[0]},
                )

            # Update the configuration entry
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
                reason="reconfigure_successful",
                description_placeholders={
                    "device_name": user_input["device_name"]
                }
            )

        # Create the schema with current values
        schema = {
            vol.Required(
                "device_name",
                default=current_config.get("device_name"),
                description={
                    "tooltip": "Enter a name for this appliance. This will be used to identify it in Home Assistant and for all related entities."
                }
            ): str,
            vol.Required(
                CONF_POWER_SENSOR,
                default=current_config.get(CONF_POWER_SENSOR),
                description={
                    "suffix": " watts",
                    "tooltip": "Select any sensor that measures power consumption. The integration will work with any numerical sensor that reports power values."
                }
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    entity_category=None,
                    domain=["sensor"],
                    multiple=False,
                )
            ),
            vol.Optional(
                "show_advanced",
                default=self._show_advanced,
                description={
                    "tooltip": "Show advanced configuration options"
                }
            ): bool,
        }

        # Add advanced options if enabled
        if self._show_advanced:
            schema.update({
                vol.Optional(
                    CONF_START_WATTS,
                    default=current_config.get(CONF_START_WATTS, DEFAULT_START_WATTS),
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
                    default=current_config.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS),
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
                    CONF_DEBOUNCE,
                    default=current_config.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE),
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
                    default=current_config.get(CONF_SERVICE_REMINDER, False),
                    description={
                        "tooltip": "Enable service reminders to track appliance usage and notify you when maintenance is needed. When enabled, you can set the number of uses before a reminder."
                    }
                ): bool,
                vol.Optional(
                    CONF_SERVICE_REMINDER_COUNT,
                    default=current_config.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT),
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
                    default=current_config.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance"),
                    description={
                        "tooltip": "Custom message to show when service is needed. If left empty, a default message will be used. The message will reset after the next use."
                    }
                ): str,
            })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(schema),
            errors=self._errors,
        )
