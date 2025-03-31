"""
Constants used throughout the Smart Dumb Appliance integration.

This module defines all the constant values used in the integration,
including configuration keys, attribute names, and default values.
"""

# Integration domain name
DOMAIN = "smart_dumb_appliance"

# Default name for the integration
DEFAULT_NAME = "Smart Dumb Appliance"

# Configuration keys
CONF_DEVICE_NAME = "device_name"
CONF_POWER_SENSOR = "power_sensor"
CONF_COST_SENSOR = "cost_sensor"
CONF_DEAD_ZONE = "dead_zone"
CONF_DEBOUNCE = "debounce"

# Attribute names for the appliance state
ATTR_START_TIME = "start_time"      # Timestamp when the appliance started running
ATTR_END_TIME = "end_time"          # Timestamp when the appliance finished running

# Default values
DEFAULT_DEAD_ZONE = 0.1
DEFAULT_DEBOUNCE = 0.5

# State attributes
ATTR_LAST_UPDATE = "last_update"    # Last time the sensor was updated
ATTR_POWER_USAGE = "power_usage"    # Current power usage in watts
ATTR_TOTAL_COST = "total_cost"      # Total cost of operation in currency units
