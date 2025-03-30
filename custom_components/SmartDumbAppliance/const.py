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
CONF_POWER_SENSOR = "power_sensor"  # Entity ID of the power consumption sensor
CONF_COST_SENSOR = "cost_sensor"    # Entity ID of the cost per kWh sensor
CONF_DEAD_ZONE = "dead_zone"        # Power threshold below which appliance is considered off
CONF_DEBOUNCE = "debounce"          # Time in seconds to wait before confirming state change
CONF_DEVICE_NAME = "device_name"    # User-friendly name for the appliance

# Attribute names for the appliance state
ATTR_START_TIME = "start_time"      # Timestamp when the appliance started running
ATTR_END_TIME = "end_time"          # Timestamp when the appliance finished running

# Default values
DEFAULT_DEAD_ZONE = 5.0            # Default power threshold in watts
DEFAULT_DEBOUNCE = 30.0            # Default debounce time in seconds

# State attributes
ATTR_LAST_UPDATE = "last_update"    # Last time the sensor was updated
ATTR_POWER_USAGE = "power_usage"    # Current power usage in watts
ATTR_TOTAL_COST = "total_cost"      # Total cost of operation in currency units
