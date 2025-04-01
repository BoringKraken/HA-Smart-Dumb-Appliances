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
CONF_DEBOUNCE = "debounce"                # Time to wait before confirming state changes
CONF_SERVICE_REMINDER = "service_reminder"  # Whether to enable service reminders
CONF_SERVICE_REMINDER_COUNT = "service_reminder_count"  # Number of uses before service reminder
CONF_SERVICE_REMINDER_MESSAGE = "service_reminder_message"  # Custom message for service reminder

# Default values for configuration options
DEFAULT_START_WATTS = 100.0               # Default start threshold (100W)
DEFAULT_STOP_WATTS = 50.0                 # Default stop threshold (50W)
DEFAULT_DEBOUNCE = 5                      # Default debounce time (5 seconds)
DEFAULT_SERVICE_REMINDER_COUNT = 100       # Default number of uses before service reminder

# Attribute names for the appliance state - these are the data points we track
ATTR_START_TIME = "start_time"            # When the appliance started running
ATTR_END_TIME = "end_time"                # When the appliance finished running
ATTR_LAST_UPDATE = "last_update"          # When we last checked the appliance's status
ATTR_POWER_USAGE = "power_usage"          # Current power consumption in watts
ATTR_TOTAL_COST = "total_cost"            # Total cost of operation in your currency
ATTR_USE_COUNT = "use_count"              # Number of times the appliance has been used
ATTR_LAST_SERVICE = "last_service"        # When the appliance was last serviced
ATTR_NEXT_SERVICE = "next_service"        # When the appliance should be serviced next
ATTR_SERVICE_MESSAGE = "service_message"   # Custom message for service reminder
ATTR_CYCLE_ENERGY = "cycle_energy"        # Energy used in the current cycle
ATTR_CYCLE_COST = "cycle_cost"            # Cost of the current cycle
ATTR_IS_RUNNING = "is_running"            # Whether the appliance is currently running
ATTR_START_WATTS = "start_watts"          # Current start threshold setting
ATTR_STOP_WATTS = "stop_watts"            # Current stop threshold setting
ATTR_DEBOUNCE = "debounce"                # Current debounce setting
ATTR_POWER_SENSOR = "power_sensor"        # Entity ID of the power sensor
ATTR_COST_SENSOR = "cost_sensor"          # Entity ID of the cost sensor
ATTR_SERVICE_REMINDER_ENABLED = "service_reminder_enabled"  # Whether service reminders are enabled
ATTR_SERVICE_REMINDER_COUNT = "service_reminder_count"      # Current service reminder count setting

# Default configuration
DEFAULT_CONFIG = {
    CONF_START_WATTS: 5.0,
    CONF_STOP_WATTS: 2.0,
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
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: False,
        CONF_SERVICE_REMINDER_COUNT: 50,
        CONF_SERVICE_REMINDER_MESSAGE: "Appliance needs maintenance",
    },
    "washer": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 50,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean washing machine filter and check hoses",
    },
    "dryer": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 2,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean lint trap and check vent hose",
    },
    "dishwasher": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 30,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean dishwasher filter and check spray arms",
    },
    "toaster": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 100,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean toaster crumb tray and check heating elements",
    },
    "coffee machine": {
        CONF_START_WATTS: 5.0,
        CONF_STOP_WATTS: 2.0,
        CONF_DEBOUNCE: 0.5,
        CONF_SERVICE_REMINDER: True,
        CONF_SERVICE_REMINDER_COUNT: 30,
        CONF_SERVICE_REMINDER_MESSAGE: "Clean coffee machine and descale if needed",
    }
}
