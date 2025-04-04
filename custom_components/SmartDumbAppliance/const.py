"""
Constants used throughout the Smart Dumb Appliance integration.

This module defines all the constant values used in the integration,
including configuration keys, attribute names, and default values.
"""

# Integration domain name - this is how Home Assistant identifies our integration
DOMAIN = "smart_dumb_appliance"

# Default name for the integration - shown in the Home Assistant UI
DEFAULT_NAME = "Smart Dumb Appliance"

# Configuration keys - these are the settings that users can configure in the UI
CONF_DEVICE_NAME = "device_name"          # The friendly name for the appliance (e.g., "Washing Machine")
CONF_POWER_SENSOR = "power_sensor"        # The sensor that measures power consumption in watts
CONF_COST_SENSOR = "cost_sensor"          # The sensor that provides cost per kWh (e.g., energy rate)
CONF_START_WATTS = "start_watts"          # Power threshold that indicates appliance has started
CONF_STOP_WATTS = "stop_watts"            # Power threshold that indicates appliance has stopped
CONF_DEAD_ZONE = "dead_zone"              # Minimum power threshold to consider appliance as "on" (safety check)
CONF_DEBOUNCE = "debounce"                # Time to wait before confirming state changes
CONF_SERVICE_REMINDER = "service_reminder"  # Whether to enable service reminders
CONF_SERVICE_REMINDER_COUNT = "service_reminder_count"  # Number of uses before service reminder
CONF_SERVICE_REMINDER_MESSAGE = "service_reminder_message"  # Custom message for service reminder

# Attribute names for the appliance state - these are the data points we track
ATTR_START_TIME = "start_time"      # When the appliance started running
ATTR_END_TIME = "end_time"          # When the appliance finished running
ATTR_LAST_UPDATE = "last_update"    # When we last checked the appliance's status
ATTR_POWER_USAGE = "power_usage"    # Current power consumption in watts
ATTR_TOTAL_COST = "total_cost"      # Total cost of operation in your currency
ATTR_USE_COUNT = "use_count"        # How many times the appliance has been used
ATTR_LAST_SERVICE = "last_service"  # When the appliance was last serviced
ATTR_NEXT_SERVICE = "next_service"  # When the appliance needs next service
ATTR_SERVICE_MESSAGE = "service_message"  # Custom message for service reminder

# Default values - these are used if the user doesn't specify their own values
DEFAULT_START_WATTS = 5.0           # Default start threshold (5 watts)
DEFAULT_STOP_WATTS = 2.0            # Default stop threshold (2 watts)
DEFAULT_DEAD_ZONE = 0.5             # Default power threshold (0.5 watts) - safety check
DEFAULT_DEBOUNCE = 5.0              # Default debounce time (5 seconds)
DEFAULT_SERVICE_REMINDER_COUNT = 50  # Default number of uses before service reminder

# Default configuration
DEFAULT_CONFIG = {
    CONF_START_WATTS: 5.0,
    CONF_STOP_WATTS: 2.0,
    CONF_DEAD_ZONE: 0.5,
    CONF_DEBOUNCE: 5.0,
    CONF_SERVICE_REMINDER: False,
    CONF_SERVICE_REMINDER_COUNT: 50,
    CONF_SERVICE_REMINDER_MESSAGE: "Appliance needs maintenance",
}

# Appliance-specific defaults
APPLIANCE_DEFAULTS = {
    "default": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: False,
        CONF_SERVICE_REMINDER_COUNT: 50,
        CONF_SERVICE_REMINDER_MESSAGE: "Appliance needs maintenance",
    },
    "washer": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 50,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean washing machine filter and check hoses",
    },
    "dryer": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 2,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean lint trap and check vent hose",
    },
    "dishwasher": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 30,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean dishwasher filter and check spray arms",
    },
    "toaster": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 100,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean toaster crumb tray and check heating elements",
    },
    "coffee machine": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEAD_ZONE: 0.1,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 30,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean coffee machine and descale if needed",
    }
}
