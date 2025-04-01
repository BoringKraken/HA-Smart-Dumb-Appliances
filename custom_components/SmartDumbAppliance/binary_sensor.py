"""Binary sensor platform for Smart Dumb Appliance.

This module provides a binary sensor that indicates whether an appliance is currently running
based on its power consumption. It tracks:
- Power state (on/off)
- Current power usage
- Last update timestamp
- Power thresholds
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_POWER_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEBOUNCE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEBOUNCE,
    CONF_DEVICE_NAME,
    ATTR_POWER_USAGE,
    ATTR_LAST_UPDATE,
    ATTR_START_TIME,
    ATTR_END_TIME,
    ATTR_USE_COUNT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance binary sensor."""
    # Create a coordinator for the binary sensor
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{entry.data.get('device_name', 'Smart Dumb Appliance')}_binary_coordinator",
        update_method=lambda: True,  # Return True to indicate successful update
        update_interval=timedelta(seconds=1),
    )
    
    # Create and add the binary sensor
    async_add_entities([SmartDumbApplianceBinarySensor(hass, entry, coordinator)])
    
    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """
    Representation of a Smart Dumb Appliance binary sensor.
    
    This binary sensor indicates whether an appliance is currently running
    based on its power consumption. It provides:
    - On/Off state based on power thresholds
    - Current power usage
    - Last update timestamp
    - Start/End times of operation
    - Usage count
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the binary sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self._attr_name = config_entry.data.get(CONF_DEVICE_NAME, "Smart Dumb Appliance")
        self._attr_unique_id = f"{config_entry.entry_id}"
        
        # Load configuration
        self._power_sensor = config_entry.data[CONF_POWER_SENSOR]
        self._start_watts = config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS)
        self._stop_watts = config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)
        self._debounce = config_entry.data.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)
        
        # Initialize state tracking
        self._last_update = None
        self._last_power = 0.0
        self._start_time = None
        self._end_time = None
        self._use_count = 0
        self._was_on = False
        self._attr_is_on = False

        # Log initialization
        _LOGGER.info(
            "Initializing %s with power sensor %s (start: %sW, stop: %sW)",
            self._attr_name,
            self._power_sensor,
            self._start_watts,
            self._stop_watts
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return entity specific state attributes.
        
        Returns:
            dict: A dictionary containing all the sensor's attributes
        """
        return {
            ATTR_POWER_USAGE: self._last_power,
            ATTR_LAST_UPDATE: self._last_update,
            ATTR_START_TIME: self._start_time,
            ATTR_END_TIME: self._end_time,
            ATTR_USE_COUNT: self._use_count,
            "power_sensor": self._power_sensor,
            "start_watts": self._start_watts,
            "stop_watts": self._stop_watts,
            "debounce": self._debounce,
        }

    async def async_update(self) -> None:
        """
        Update the binary sensor state.
        
        This method is called by the coordinator to update the sensor's state
        and attributes. It:
        1. Gets the current power reading
        2. Updates the last update timestamp
        3. Determines if the appliance is running
        4. Tracks start/end times and usage count
        5. Logs state changes for debugging
        """
        try:
            # Get current power reading
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                return

            current_power = float(power_state.state)
            self._last_power = current_power
            self._last_update = datetime.now()

            # Determine if the appliance is running
            is_on = self._start_watts <= current_power <= self._stop_watts
            
            # Track state changes
            if is_on and not self._was_on:
                self._start_time = self._last_update
                self._end_time = None
                _LOGGER.debug(
                    "%s turned on (Power: %.1fW, Start: %sW, Stop: %sW)",
                    self._attr_name,
                    current_power,
                    self._start_watts,
                    self._stop_watts
                )
            elif not is_on and self._was_on:
                self._end_time = self._last_update
                self._use_count += 1
                _LOGGER.debug(
                    "%s turned off (Power: %.1fW, Duration: %s, Total uses: %d)",
                    self._attr_name,
                    current_power,
                    self._end_time - self._start_time if self._start_time else "unknown",
                    self._use_count
                )
            
            self._was_on = is_on
            self._attr_is_on = is_on

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error updating binary sensor: %s", err)
            return 