"""Cycle cost sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SmartDumbApplianceCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance cycle cost sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartDumbApplianceCostSensor(coordinator, config_entry)])

class SmartDumbApplianceCostSensor(SensorEntity):
    """Sensor representing the cycle cost of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cycle cost sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle Cost"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "USD"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:currency-usd"
        self._attr_extra_state_attributes = {
            "current_cycle_cost": 0.0,
            "previous_cycle_cost": 0.0,
            "total_cost": 0.0,
            "last_update": None,
        }

    @property
    def native_value(self) -> float:
        """Return the current cycle cost."""
        if self.coordinator.data is None:
            return 0.0
        return self.coordinator.data.cycle_cost

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_cycle_cost": data.cycle_cost,
            "previous_cycle_cost": data.previous_cycle_cost,
            "total_cost": data.total_cost,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 