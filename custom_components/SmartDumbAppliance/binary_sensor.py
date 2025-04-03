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
from homeassistant.core import HomeAssistant, callback
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
    DOMAIN,
)
from .coordinator import SmartDumbApplianceCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance binary sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartDumbApplianceBinarySensor(coordinator, config_entry)])

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """Binary sensor representing the cycle state of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle State"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_state"
        self._attr_device_class = "power"
        self._attr_icon = "mdi:power"
        self._attr_extra_state_attributes = {
            "current_power": 0.0,
            "start_time": None,
            "end_time": None,
            "cycle_duration": None,
            "cycle_energy": 0.0,
            "cycle_cost": 0.0,
            "last_update": None,
        }

    @property
    def is_on(self) -> bool:
        """Return True if the appliance is running."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.is_running

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_power": data.power_state,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "cycle_duration": data.cycle_duration,
            "cycle_energy": data.cycle_energy,
            "cycle_cost": data.cycle_cost,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 