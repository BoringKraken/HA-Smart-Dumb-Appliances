"""
Configuration flow for Smart Dumb Appliance.

This module handles the configuration flow for the Smart Dumb Appliance integration.
It provides a user interface for:
1. Setting up new appliances
2. Configuring power monitoring
3. Setting up service reminders
4. Reconfiguring existing appliances
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    NumberSelector,
    NumberSelectorConfig,
    BooleanSelector,
    BooleanSelectorConfig,
)

from .const import (
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEAD_ZONE,
    CONF_DEBOUNCE,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT,
    APPLIANCE_DEFAULTS,
)

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

def get_appliance_defaults(device_name: str) -> dict[str, Any]:
    """
    Get the default configuration for a specific appliance type.
    
    Args:
        device_name: The name of the appliance
        
    Returns:
        dict: The default configuration for the appliance
    """
    # Convert to lowercase for case-insensitive matching
    device_name = device_name.lower()
    
    # Check for exact matches first
    if device_name in APPLIANCE_DEFAULTS:
        return APPLIANCE_DEFAULTS[device_name]
    
    # Check for partial matches
    for key in APPLIANCE_DEFAULTS:
        if key in device_name or device_name in key:
            return APPLIANCE_DEFAULTS[key]
    
    # Return default configuration if no match found
    return APPLIANCE_DEFAULTS["default"]

def validate_watt_thresholds(data: dict[str, Any]) -> list[str]:
    """
    Validate the watt thresholds to ensure they make sense.
    
    Args:
        data: The configuration data
        
    Returns:
        list: List of error messages, empty if valid
    """
    errors = []
    
    # Get the values, using defaults if not provided
    start_watts = float(data.get(CONF_START_WATTS, DEFAULT_START_WATTS))
    stop_watts = float(data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS))
    dead_zone = float(data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE))
    
    # Check that stop watts is less than start watts
    if stop_watts >= start_watts:
        errors.append("Stop watts must be less than start watts")
    
    # Check that dead zone is less than stop watts
    if dead_zone >= stop_watts:
        errors.append("Dead zone must be less than stop watts")
    
    return errors

def get_power_sensors(hass: HomeAssistant) -> list[str]:
    """
    Get all available entities that could be used as power sensors.
    No restrictions on device class or unit of measurement.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        list: List of entity IDs
    """
    entity_registry = er.async_get(hass)
    return [entity.entity_id for entity in entity_registry.entities.values()]

class SmartDumbApplianceConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Smart Dumb Appliance."""

    VERSION = 1
    DOMAIN = "smart_dumb_appliance"

    def __init__(self):
        """Initialize the configuration flow."""
        self._show_advanced = False
        self._appliance_defaults = None

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
            
            # Get appliance defaults if device name is provided
            if "device_name" in user_input and not self._appliance_defaults:
                self._appliance_defaults = get_appliance_defaults(user_input["device_name"])
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
            ): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.TEXT,
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
            ): EntitySelector(
                EntitySelectorConfig(
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
            ): BooleanSelector(
                BooleanSelectorConfig()
            ),
        }

        # Add advanced options if enabled
        if self._show_advanced:
            defaults = self._appliance_defaults or get_appliance_defaults(user_input.get("device_name", ""))
            schema.update({
                vol.Optional(
                    CONF_START_WATTS,
                    default=user_input.get(CONF_START_WATTS, defaults.get(CONF_START_WATTS, DEFAULT_START_WATTS)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts. When power exceeds this value, the appliance is considered 'on'."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_STOP_WATTS,
                    default=user_input.get(CONF_STOP_WATTS, defaults.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts. When power drops below this value, the appliance is considered 'off'."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEAD_ZONE,
                    default=user_input.get(CONF_DEAD_ZONE, defaults.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Minimum power threshold to consider appliance as 'on'. Must be lower than stop watts. Prevents false readings from standby power."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEBOUNCE,
                    default=user_input.get(CONF_DEBOUNCE, defaults.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)),
                    description={
                        "suffix": " seconds",
                        "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling from power fluctuations. Higher values make the detection more stable but less responsive."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="seconds",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER,
                    default=user_input.get(CONF_SERVICE_REMINDER, defaults.get(CONF_SERVICE_REMINDER, False)),
                    description={
                        "tooltip": "Enable service reminders to track appliance usage and notify you when maintenance is needed. When enabled, you can set the number of uses before a reminder."
                    }
                ): BooleanSelector(
                    BooleanSelectorConfig()
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_COUNT,
                    default=user_input.get(CONF_SERVICE_REMINDER_COUNT, defaults.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)),
                    description={
                        "tooltip": "Number of times the appliance can be used before showing a service reminder. Only applies if service reminders are enabled."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=1000,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_MESSAGE,
                    default=user_input.get(CONF_SERVICE_REMINDER_MESSAGE, defaults.get(CONF_SERVICE_REMINDER_MESSAGE)),
                    description={
                        "tooltip": "Custom message to show when service is needed. If left empty, a default message will be used. The message will reset after the next use."
                    }
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
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
        
        Args:
            user_input: The user's input data
            
        Returns:
            FlowResult: The flow result
        """
        # Get the current entry
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            # If user toggled advanced options, show them
            if "show_advanced" in user_input:
                self._show_advanced = user_input["show_advanced"]
                return await self.async_step_reconfigure(None)
            
            # Validate the watt thresholds
            threshold_errors = validate_watt_thresholds(user_input)
            if threshold_errors:
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=self._get_schema(entry.data),
                    errors={"base": threshold_errors[0]},
                )
            
            # Update the configuration entry
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
                reason="reconfigure_successful",
                description_placeholders={"name": user_input["device_name"]},
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

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_schema(entry.data),
            errors={},
        )

    def _get_schema(self, current_data: dict[str, Any]) -> vol.Schema:
        """
        Get the schema for the configuration form.
        
        Args:
            current_data: The current configuration data
            
        Returns:
            vol.Schema: The schema for the form
        """
        # Get all power sensors
        power_sensors = get_power_sensors(self.hass)

        schema = {
            vol.Required(
                "device_name",
                default=current_data.get("device_name"),
                description={
                    "tooltip": "Enter a name for this appliance. This will be used to identify it in Home Assistant and for all related entities."
                }
            ): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.TEXT,
                    autocomplete="off",
                )
            ),
            vol.Required(
                CONF_POWER_SENSOR,
                default=current_data.get(CONF_POWER_SENSOR),
                description={
                    "suffix": " watts",
                    "tooltip": "Select any sensor that measures power consumption. The integration will work with any numerical sensor that reports power values."
                }
            ): EntitySelector(
                EntitySelectorConfig(
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
            ): BooleanSelector(
                BooleanSelectorConfig()
            ),
        }

        # Add advanced options if enabled
        if self._show_advanced:
            defaults = get_appliance_defaults(current_data.get("device_name", ""))
            schema.update({
                vol.Optional(
                    CONF_START_WATTS,
                    default=current_data.get(CONF_START_WATTS, defaults.get(CONF_START_WATTS, DEFAULT_START_WATTS)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has started. Must be higher than stop watts. When power exceeds this value, the appliance is considered 'on'."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_STOP_WATTS,
                    default=current_data.get(CONF_STOP_WATTS, defaults.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Power threshold that indicates the appliance has stopped. Must be lower than start watts. When power drops below this value, the appliance is considered 'off'."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEAD_ZONE,
                    default=current_data.get(CONF_DEAD_ZONE, defaults.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)),
                    description={
                        "suffix": " watts",
                        "tooltip": "Minimum power threshold to consider appliance as 'on'. Must be lower than stop watts. Prevents false readings from standby power."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.1,
                        max=10000,
                        step=0.1,
                        unit_of_measurement="watts",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_DEBOUNCE,
                    default=current_data.get(CONF_DEBOUNCE, defaults.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)),
                    description={
                        "suffix": " seconds",
                        "tooltip": "Time to wait before confirming state changes. Prevents rapid on/off cycling from power fluctuations. Higher values make the detection more stable but less responsive."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="seconds",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER,
                    default=current_data.get(CONF_SERVICE_REMINDER, defaults.get(CONF_SERVICE_REMINDER, False)),
                    description={
                        "tooltip": "Enable service reminders to track appliance usage and notify you when maintenance is needed. When enabled, you can set the number of uses before a reminder."
                    }
                ): BooleanSelector(
                    BooleanSelectorConfig()
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_COUNT,
                    default=current_data.get(CONF_SERVICE_REMINDER_COUNT, defaults.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)),
                    description={
                        "tooltip": "Number of times the appliance can be used before showing a service reminder. Only applies if service reminders are enabled."
                    }
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=1000,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SERVICE_REMINDER_MESSAGE,
                    default=current_data.get(CONF_SERVICE_REMINDER_MESSAGE, defaults.get(CONF_SERVICE_REMINDER_MESSAGE)),
                    description={
                        "tooltip": "Custom message to show when service is needed. If left empty, a default message will be used. The message will reset after the next use."
                    }
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        autocomplete="off",
                    )
                ),
            })

        return vol.Schema(schema)
