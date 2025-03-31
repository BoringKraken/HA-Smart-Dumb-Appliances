"""
Constants for Smart Dumb Appliance integration.

This module defines all the constants used throughout the integration,
including configuration keys, default values, and attribute names.
"""

from typing import Final

# Domain name for the integration
DOMAIN: Final = "smart_dumb_appliance"

# Configuration keys
CONF_POWER_SENSOR: Final = "power_sensor"
CONF_COST_SENSOR: Final = "cost_sensor"
CONF_START_WATTS: Final = "start_watts"
CONF_STOP_WATTS: Final = "stop_watts"
CONF_DEAD_ZONE: Final = "dead_zone"
CONF_DEBOUNCE: Final = "debounce"
CONF_SERVICE_REMINDER: Final = "service_reminder"
CONF_SERVICE_REMINDER_COUNT: Final = "service_reminder_count"
CONF_SERVICE_REMINDER_MESSAGE: Final = "service_reminder_message"

# Default values
DEFAULT_START_WATTS: Final = 5.0
DEFAULT_STOP_WATTS: Final = 2.0
DEFAULT_DEAD_ZONE: Final = 1.0
DEFAULT_DEBOUNCE: Final = 5
DEFAULT_SERVICE_REMINDER_COUNT: Final = 30

# Attribute names
ATTR_POWER_USAGE: Final = "power_usage"
ATTR_TOTAL_COST: Final = "total_cost"
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_START_TIME: Final = "start_time"
ATTR_END_TIME: Final = "end_time"
ATTR_USE_COUNT: Final = "use_count"
ATTR_LAST_SERVICE: Final = "last_service"
ATTR_NEXT_SERVICE: Final = "next_service"
ATTR_SERVICE_MESSAGE: Final = "service_message"

# Appliance-specific default configurations
APPLIANCE_DEFAULTS: Final = {
    # Kitchen appliances
    "dishwasher": {
        "start_watts": 1200.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 30,
        "service_reminder_message": "Time to clean the filter and check for debris",
    },
    "washing machine": {
        "start_watts": 500.0,
        "stop_watts": 50.0,
        "dead_zone": 25.0,
        "service_reminder": True,
        "service_reminder_count": 30,
        "service_reminder_message": "Time to clean the filter and check for debris",
    },
    "dryer": {
        "start_watts": 3000.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 2,
        "service_reminder_message": "Time to clean the lint trap",
    },
    "refrigerator": {
        "start_watts": 150.0,
        "stop_watts": 50.0,
        "dead_zone": 25.0,
        "service_reminder": True,
        "service_reminder_count": 90,
        "service_reminder_message": "Time to clean the coils and check seals",
    },
    "freezer": {
        "start_watts": 150.0,
        "stop_watts": 50.0,
        "dead_zone": 25.0,
        "service_reminder": True,
        "service_reminder_count": 90,
        "service_reminder_message": "Time to defrost and clean",
    },
    "oven": {
        "start_watts": 2400.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 20,
        "service_reminder_message": "Time to clean the oven",
    },
    "microwave": {
        "start_watts": 1000.0,
        "stop_watts": 50.0,
        "dead_zone": 25.0,
        "service_reminder": True,
        "service_reminder_count": 50,
        "service_reminder_message": "Time to clean the microwave",
    },
    
    # HVAC
    "air conditioner": {
        "start_watts": 1500.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 90,
        "service_reminder_message": "Time to clean the filter and check refrigerant",
    },
    "heater": {
        "start_watts": 1500.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 90,
        "service_reminder_message": "Time to clean the filter and check for debris",
    },
    "heat pump": {
        "start_watts": 1500.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 90,
        "service_reminder_message": "Time to clean the filter and check refrigerant",
    },
    
    # Water heating
    "water heater": {
        "start_watts": 4500.0,
        "stop_watts": 100.0,
        "dead_zone": 50.0,
        "service_reminder": True,
        "service_reminder_count": 180,
        "service_reminder_message": "Time to flush the tank and check anode rod",
    },
    
    # Default configuration for unknown appliances
    "default": {
        "start_watts": DEFAULT_START_WATTS,
        "stop_watts": DEFAULT_STOP_WATTS,
        "dead_zone": DEFAULT_DEAD_ZONE,
        "service_reminder": False,
        "service_reminder_count": DEFAULT_SERVICE_REMINDER_COUNT,
        "service_reminder_message": "Time for maintenance",
    },
}
