"""Cycle duration sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmartDumbApplianceCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance cycle duration sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartDumbApplianceDurationSensor(coordinator, config_entry)])

class SmartDumbApplianceDurationSensor(SensorEntity):
    """Sensor representing the cycle duration of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cycle duration sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle Duration"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_duration"
        self._attr_icon = "mdi:timer"
        self._attr_extra_state_attributes = {
            "current_cycle_duration": None,
            "previous_cycle_duration": None,
            "total_duration": timedelta(0),
            "last_update": None,
        }

    @property
    def native_value(self) -> timedelta | None:
        """Return the current cycle duration."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.cycle_duration

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_cycle_duration": data.cycle_duration,
            "previous_cycle_duration": data.last_cycle_duration,
            "total_duration": data.total_duration,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 