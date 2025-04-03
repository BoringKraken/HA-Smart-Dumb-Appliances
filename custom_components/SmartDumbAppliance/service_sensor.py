"""Service status sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
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
    """Set up the Smart Dumb Appliance service status sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartDumbApplianceServiceSensor(coordinator, config_entry)])

class SmartDumbApplianceServiceSensor(SensorEntity):
    """Sensor representing the service status of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the service status sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Service Status"
        self._attr_unique_id = f"{config_entry.entry_id}_service_status"
        self._attr_icon = "mdi:wrench"
        self._attr_extra_state_attributes = {
            "cycle_count": 0,
            "service_reminder_enabled": False,
            "service_reminder_message": "",
            "total_cycles_till_service": 0,
            "remaining_cycles": 0,
            "current_running_state": False,
            "last_update": None,
        }

    @property
    def native_value(self) -> str:
        """Return the service status."""
        if self.coordinator.data is None:
            return "ok"
        return self.coordinator.data.service_status

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "cycle_count": data.use_count,
            "service_reminder_enabled": data.service_reminder_enabled,
            "service_reminder_message": data.service_reminder_message,
            "total_cycles_till_service": data.service_reminder_count,
            "remaining_cycles": data.remaining_cycles,
            "current_running_state": data.is_running,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 