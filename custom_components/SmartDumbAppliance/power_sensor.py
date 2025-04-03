"""Current power sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfPower

from .coordinator import SmartDumbApplianceCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance current power sensor from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([SmartDumbAppliancePowerSensor(coordinator, config_entry)])

class SmartDumbAppliancePowerSensor(SensorEntity):
    """Sensor representing the current power usage of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the current power sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Current Power"
        self._attr_unique_id = f"{config_entry.entry_id}_current_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_extra_state_attributes = {
            "start_threshold": config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS),
            "stop_threshold": config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS),
            "running_state": False,
            "power_sensor": config_entry.data[CONF_POWER_SENSOR],
            "last_update": None,
        }

    @property
    def native_value(self) -> float:
        """Return the current power usage."""
        if self.coordinator.data is None:
            return 0.0
        return self.coordinator.data.power_state

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "running_state": data.is_running,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 