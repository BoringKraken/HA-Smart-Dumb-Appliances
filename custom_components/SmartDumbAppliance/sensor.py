"""
Sensor platform for Smart Dumb Appliance.

This module creates the main sensor that monitors an appliance's energy usage.
It tracks:
- Total energy consumption in kWh
- Current power usage in watts
- Cost of operation (if cost sensor is configured)
- Start and end times of operation
- Number of uses
- Service reminders
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import (
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_DEAD_ZONE,
    CONF_DEBOUNCE,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT,
    ATTR_POWER_USAGE,
    ATTR_TOTAL_COST,
    ATTR_LAST_UPDATE,
    ATTR_START_TIME,
    ATTR_END_TIME,
    ATTR_USE_COUNT,
    ATTR_LAST_SERVICE,
    ATTR_NEXT_SERVICE,
    ATTR_SERVICE_MESSAGE
)

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Smart Dumb Appliance sensor.
    
    This function is called when Home Assistant is setting up the integration.
    It creates a new sensor entity for each configured appliance.
    """
    async_add_entities([SmartDumbApplianceSensor(entry)])

class SmartDumbApplianceSensor(SensorEntity):
    """
    Representation of a Smart Dumb Appliance sensor.
    
    This class creates a sensor that monitors an appliance's energy usage.
    It tracks power consumption, calculates energy usage and costs,
    and manages service reminders.
    """

    def __init__(self, entry: ConfigEntry) -> None:
        """
        Initialize the sensor.
        
        This method sets up the sensor with all the configuration options
        from the user's setup in the Home Assistant UI.
        """
        # Store the configuration entry for reference
        self._entry = entry
        
        # Set up the basic sensor attributes
        self._attr_name = entry.data.get("device_name", "Smart Dumb Appliance")
        self._attr_unique_id = f"{entry.entry_id}_sensor"
        self._attr_native_value = 0.0
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"
        
        # Load configuration from the entry
        self._power_sensor = entry.data[CONF_POWER_SENSOR]  # Required power sensor
        self._cost_sensor = entry.data.get(CONF_COST_SENSOR)  # Optional cost sensor
        self._dead_zone = entry.data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)  # Power threshold
        self._debounce = entry.data.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)  # Time to wait
        self._service_reminder = entry.data.get(CONF_SERVICE_REMINDER, False)  # Enable reminders
        self._service_reminder_count = entry.data.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)
        self._service_reminder_message = entry.data.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance")
        
        # Initialize state tracking variables
        self._last_update = None  # Last time we checked the sensor
        self._last_power = 0.0    # Last power reading
        self._total_energy = 0.0  # Total energy used
        self._total_cost = 0.0    # Total cost of operation
        self._start_time = None   # When the appliance started
        self._end_time = None     # When the appliance finished
        self._use_count = 0       # Number of times used
        self._last_service = None # Last service date
        self._next_service = None # Next service date
        self._was_on = False      # Previous power state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return additional state attributes.
        
        These attributes provide extra information about the appliance's
        current state and usage history.
        """
        return {
            ATTR_POWER_USAGE: self._last_power,  # Current power usage
            ATTR_TOTAL_COST: self._total_cost,    # Total cost so far
            ATTR_LAST_UPDATE: self._last_update,  # Last check time
            ATTR_START_TIME: self._start_time,    # When it started
            ATTR_END_TIME: self._end_time,        # When it finished
            ATTR_USE_COUNT: self._use_count,      # Number of uses
            ATTR_LAST_SERVICE: self._last_service,  # Last service date
            ATTR_NEXT_SERVICE: self._next_service,  # Next service date
            ATTR_SERVICE_MESSAGE: self._service_reminder_message if self._service_reminder else None,
        }

    async def async_update(self) -> None:
        """
        Update the sensor state.
        
        This method is called regularly by Home Assistant to update the
        sensor's state. It:
        1. Checks the current power usage
        2. Detects when the appliance turns on/off
        3. Calculates energy usage and costs
        4. Manages service reminders
        """
        try:
            # Get the current power reading from the configured sensor
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                return

            # Convert the power reading to a number
            current_power = float(power_state.state)
            self._last_power = current_power
            now = datetime.now()
            self._last_update = now

            # Check if the appliance is currently on
            is_on = current_power > self._dead_zone
            
            # Handle state changes (on/off)
            if is_on and not self._was_on:
                # Appliance just turned on - record start time
                self._start_time = now
                self._end_time = None
            elif not is_on and self._was_on:
                # Appliance just turned off - record end time and increment use count
                self._end_time = now
                self._use_count += 1
                
                # Check if we need to show a service reminder
                if self._service_reminder and self._use_count >= self._service_reminder_count:
                    self._last_service = self._next_service or now
                    self._next_service = now + timedelta(days=1)  # Set next service to tomorrow
                    _LOGGER.info(
                        "Service reminder for %s: %s",
                        self._attr_name,
                        self._service_reminder_message
                    )
            
            # Store the current state for next update
            self._was_on = is_on

            # Calculate energy usage if the appliance is on
            if is_on and self._start_time is not None:
                # Calculate how long the appliance has been running
                delta = (now - self._start_time).total_seconds()
                if delta > self._debounce:
                    # Convert power and time to energy (kWh)
                    energy = (current_power * delta) / 3600000  # Convert to kWh
                    self._total_energy += energy

                    # Calculate cost if cost sensor is configured
                    if self._cost_sensor:
                        cost_state = self.hass.states.get(self._cost_sensor)
                        if cost_state is not None:
                            cost_per_kwh = float(cost_state.state)
                            self._total_cost += energy * cost_per_kwh

            # Update the main sensor value (total energy used)
            self._attr_native_value = self._total_energy

        except (ValueError, TypeError) as err:
            # Log any errors that occur during update
            _LOGGER.error("Error updating sensor: %s", err)
            return 