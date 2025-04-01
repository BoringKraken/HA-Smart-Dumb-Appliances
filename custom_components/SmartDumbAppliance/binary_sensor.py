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

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
from .coordinator import SmartDumbApplianceCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance binary sensor from a config entry."""
    # Get the configuration data
    config = config_entry.data
    device_name = config[CONF_DEVICE_NAME]

    # Get the coordinator from hass.data
    coordinator = hass.data["smart_dumb_appliance"][config_entry.entry_id]

    # Create and add the binary sensor
    async_add_entities([SmartDumbApplianceBinarySensor(hass, config_entry, coordinator)])

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """
    Binary sensor for tracking if an appliance is running.
    
    This binary sensor indicates whether an appliance is currently running
    based on its power consumption. It provides:
    - On/Off state based on power thresholds
    - Current power usage
    - Last update timestamp
    - Start/End times of operation
    - Power sensor configuration
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: SmartDumbApplianceCoordinator,
    ) -> None:
        """
        Initialize the binary sensor.
        
        Args:
            hass: The Home Assistant instance
            config_entry: The configuration entry containing all settings
            coordinator: The update coordinator for managing updates
        """
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self._attr_name = f"{config_entry.data.get(CONF_DEVICE_NAME, 'Smart Dumb Appliance')} Power State"
        self._attr_unique_id = f"{self._attr_name.lower().replace(' ', '_')}_power_state"
        self._attr_device_class = BinarySensorDeviceClass.POWER
        self._attr_has_entity_name = True
        self._attr_translation_key = "power_state"
        
        # Define all possible attributes that this sensor can have
        self._attr_extra_state_attributes = {
            # Current state
            "power_usage": 0.0,
            
            # Timing information
            "last_update": None,
            "start_time": None,
            "end_time": None,
            
            # Configuration
            "power_sensor": config_entry.data[CONF_POWER_SENSOR],
        }

    @property
    def should_poll(self) -> bool:
        """Return False as we use the coordinator for updates."""
        return False

    async def async_update(self) -> None:
        """Update the binary sensor state."""
        if not self.coordinator.last_update_success:
            _LOGGER.debug(
                "Binary sensor %s update skipped - coordinator update not successful",
                self._attr_name
            )
            return

        data = self.coordinator.data
        if data is None:
            _LOGGER.debug(
                "Binary sensor %s update skipped - no data available from coordinator",
                self._attr_name
            )
            return

        # Log the incoming data
        _LOGGER.debug(
            "Binary sensor %s received update - Power: %.1fW, Running: %s, "
            "Start time: %s, End time: %s, Use count: %d",
            self._attr_name,
            data.power_state,
            data.is_running,
            data.start_time,
            data.end_time,
            data.use_count
        )

        # Update the state
        old_state = self._attr_is_on
        self._attr_is_on = data.is_running
        
        # Update attributes
        self._attr_extra_state_attributes.update({
            ATTR_POWER_USAGE: data.power_state,
            ATTR_LAST_UPDATE: data.last_update,
            ATTR_START_TIME: data.start_time,
            ATTR_END_TIME: data.end_time,
            ATTR_USE_COUNT: data.use_count,
        })

        # Log state change if it occurred
        if old_state != self._attr_is_on:
            _LOGGER.debug(
                "Binary sensor %s state changed - Old: %s, New: %s, Power: %.1fW",
                self._attr_name,
                old_state,
                self._attr_is_on,
                data.power_state
            )
        else:
            _LOGGER.debug(
                "Binary sensor %s state unchanged - State: %s, Power: %.1fW",
                self._attr_name,
                self._attr_is_on,
                data.power_state
            ) 