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
    CONF_DEAD_ZONE,
    DEFAULT_DEAD_ZONE,
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
    async_add_entities([SmartDumbApplianceBinarySensor(entry, coordinator)])
    
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

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator) -> None:
        """
        Initialize the binary sensor.
        
        Args:
            entry: The configuration entry containing all settings
            coordinator: The update coordinator for managing updates
        """
        self._entry = entry
        self._coordinator = coordinator
        self._attr_name = f"{entry.data.get('device_name', 'Smart Dumb Appliance')} Status"
        self._attr_unique_id = f"{entry.entry_id}_binary_sensor"
        self._attr_is_on = False
        self._attr_should_poll = False  # We rely on the coordinator for updates
        
        # Configuration
        self._power_sensor = entry.data[CONF_POWER_SENSOR]
        self._dead_zone = entry.data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)
        
        # State tracking
        self._last_update = None
        self._last_power = 0.0
        self._start_time = None
        self._end_time = None
        self._use_count = 0
        self._was_on = False

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
            "dead_zone": self._dead_zone,
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
            is_on = current_power > self._dead_zone
            
            # Track state changes
            if is_on and not self._was_on:
                self._start_time = self._last_update
                self._end_time = None
                _LOGGER.debug(
                    "%s turned on (Power: %.1fW, Dead zone: %.1fW)",
                    self._attr_name,
                    current_power,
                    self._dead_zone
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