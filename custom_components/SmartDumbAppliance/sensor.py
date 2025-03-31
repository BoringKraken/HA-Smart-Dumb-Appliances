"""Sensor platform for Smart Dumb Appliance."""
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
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE,
    ATTR_POWER_USAGE,
    ATTR_TOTAL_COST,
    ATTR_LAST_UPDATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance sensor."""
    async_add_entities([SmartDumbApplianceSensor(entry)])

class SmartDumbApplianceSensor(SensorEntity):
    """Representation of a Smart Dumb Appliance sensor."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_name = entry.data.get("device_name", "Smart Dumb Appliance")
        self._attr_unique_id = f"{entry.entry_id}_sensor"
        self._attr_native_value = 0.0
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"
        
        # Configuration
        self._power_sensor = entry.data[CONF_POWER_SENSOR]
        self._cost_sensor = entry.data.get(CONF_COST_SENSOR)
        self._dead_zone = entry.data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)
        self._debounce = entry.data.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)
        
        # State tracking
        self._last_update = None
        self._last_power = 0.0
        self._total_energy = 0.0
        self._total_cost = 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            ATTR_POWER_USAGE: self._last_power,
            ATTR_TOTAL_COST: self._total_cost,
            ATTR_LAST_UPDATE: self._last_update,
        }

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            # Get current power reading
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                return

            current_power = float(power_state.state)
            self._last_power = current_power

            # Update energy consumption if power is above dead zone
            if current_power > self._dead_zone:
                now = datetime.now()
                if self._last_update is not None:
                    delta = (now - self._last_update).total_seconds()
                    if delta > self._debounce:
                        # Calculate energy in kWh
                        energy = (current_power * delta) / 3600000  # Convert to kWh
                        self._total_energy += energy

                        # Calculate cost if cost sensor is configured
                        if self._cost_sensor:
                            cost_state = self.hass.states.get(self._cost_sensor)
                            if cost_state is not None:
                                cost_per_kwh = float(cost_state.state)
                                self._total_cost += energy * cost_per_kwh

                self._last_update = now

            # Update the sensor value
            self._attr_native_value = self._total_energy

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error updating sensor: %s", err)
            return 