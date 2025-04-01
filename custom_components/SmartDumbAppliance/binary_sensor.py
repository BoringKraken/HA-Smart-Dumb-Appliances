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
        """
        Update the binary sensor state.
        
        This method is called by the coordinator to update the sensor's state
        and attributes. It:
        1. Gets the latest data from the coordinator
        2. Updates the binary state (on/off)
        3. Updates all relevant attributes
        4. Logs state changes for debugging
        """
        try:
            # Wait for the coordinator to update
            await self.coordinator.async_request_refresh()
            
            # Get the latest data from the coordinator
            data = self.coordinator.data
            if data is None:
                _LOGGER.warning("No data available from coordinator for %s", self._attr_name)
                return

            # Update the binary state
            self._attr_is_on = data.is_running
            
            # Update all attributes with the latest values
            self._attr_extra_state_attributes.update({
                # Current state
                "power_usage": data.power_state,
                
                # Timing information
                "last_update": data.last_update,
                "start_time": data.start_time,
                "end_time": data.end_time,
            })
            
            # Log the update for debugging
            _LOGGER.debug(
                "Updated binary sensor for %s: %s (current: %.1fW, last_update: %s)",
                self._attr_name,
                "on" if data.is_running else "off",
                data.power_state,
                data.last_update
            )

        except Exception as err:
            _LOGGER.error(
                "Error updating binary sensor %s: %s",
                self._attr_name,
                err
            ) 