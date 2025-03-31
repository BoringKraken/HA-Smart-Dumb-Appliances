"""Binary sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_POWER_SENSOR,
    CONF_DEAD_ZONE,
    DEFAULT_DEAD_ZONE,
    ATTR_POWER_USAGE,
    ATTR_LAST_UPDATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance binary sensor."""
    async_add_entities([SmartDumbApplianceBinarySensor(entry)])

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """Representation of a Smart Dumb Appliance binary sensor."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._entry = entry
        self._attr_name = f"{entry.data.get('device_name', 'Smart Dumb Appliance')} Status"
        self._attr_unique_id = f"{entry.entry_id}_binary_sensor"
        self._attr_is_on = False
        
        # Configuration
        self._power_sensor = entry.data[CONF_POWER_SENSOR]
        self._dead_zone = entry.data.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE)
        
        # State tracking
        self._last_update = None
        self._last_power = 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            ATTR_POWER_USAGE: self._last_power,
            ATTR_LAST_UPDATE: self._last_update,
        }

    async def async_update(self) -> None:
        """Update the binary sensor state."""
        try:
            # Get current power reading
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                return

            current_power = float(power_state.state)
            self._last_power = current_power
            self._last_update = datetime.now()

            # Update the binary sensor state
            self._attr_is_on = current_power > self._dead_zone

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error updating binary sensor: %s", err)
            return 