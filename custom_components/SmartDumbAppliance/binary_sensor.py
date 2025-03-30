"""
Binary Sensor implementation for Smart Dumb Appliance.

This module provides a binary sensor that indicates whether an appliance is running
based on its power consumption. The sensor uses a dead zone threshold and debounce
time to avoid false triggers from power fluctuations.
"""

import logging
import time
from typing import Optional
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_POWER_SENSOR,
    CONF_DEAD_ZONE,
    CONF_DEBOUNCE,
    CONF_DEVICE_NAME,
    DEFAULT_DEAD_ZONE,
    DEFAULT_DEBOUNCE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """
    Set up the binary sensor from a ConfigEntry.
    
    Args:
        hass: The Home Assistant instance
        entry: The ConfigEntry containing the configuration
        async_add_entities: Callback to add entities to Home Assistant
    """
    try:
        config = hass.data[DOMAIN][entry.entry_id]
        device_name = config.get(CONF_DEVICE_NAME, "Appliance")
        power_sensor_id = config.get(CONF_POWER_SENSOR)
        dead_zone = float(config.get(CONF_DEAD_ZONE, DEFAULT_DEAD_ZONE))
        debounce = float(config.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE))

        if not power_sensor_id:
            _LOGGER.error("No power sensor specified for %s", device_name)
            return

        sensor = SmartDumbApplianceBinarySensor(
            entry_id=entry.entry_id,
            name=f"{device_name} Running",
            power_sensor_entity_id=power_sensor_id,
            dead_zone=dead_zone,
            debounce=debounce
        )

        async_add_entities([sensor], update_before_add=True)
        _LOGGER.debug("Successfully set up binary sensor for %s", device_name)
        
    except Exception as e:
        _LOGGER.error("Error setting up binary sensor: %s", str(e))

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """
    Binary Sensor that indicates if an appliance is running based on power consumption.
    
    The sensor considers an appliance to be running when its power consumption is above
    the dead zone threshold for longer than the debounce time.
    """

    def __init__(
        self,
        entry_id: str,
        name: str,
        power_sensor_entity_id: str,
        dead_zone: float,
        debounce: float
    ):
        """
        Initialize the binary sensor.
        
        Args:
            entry_id: The unique identifier for this configuration entry
            name: The display name for the sensor
            power_sensor_entity_id: The entity ID of the power consumption sensor
            dead_zone: Power threshold below which appliance is considered off
            debounce: Time in seconds to wait before confirming state change
        """
        self._entry_id = entry_id
        self._name = name
        self._power_sensor_entity_id = power_sensor_entity_id
        self._dead_zone = dead_zone
        self._debounce = debounce

        self._state = False
        self._last_above_threshold = 0
        self._attr_unique_id = f"{entry_id}_running_binary"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return whether the appliance is considered running."""
        return self._state

    @property
    def should_poll(self) -> bool:
        """Return True to enable polling for updates."""
        return True

    async def async_update(self) -> None:
        """
        Update the sensor state based on power consumption.
        
        This method checks the power consumption sensor and updates the binary
        sensor state based on the dead zone threshold and debounce time.
        """
        try:
            power_state_obj = self.hass.states.get(self._power_sensor_entity_id)
            if not power_state_obj or power_state_obj.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                _LOGGER.warning("Power sensor %s is unavailable", self._power_sensor_entity_id)
                return

            usage = float(power_state_obj.state)
            current_time = time.time()

            if usage > self._dead_zone:
                self._last_above_threshold = current_time
                self._state = True
            else:
                if (current_time - self._last_above_threshold) > self._debounce:
                    self._state = False

        except ValueError as e:
            _LOGGER.error("Invalid power value from sensor %s: %s", self._power_sensor_entity_id, str(e))
        except Exception as e:
            _LOGGER.error("Error updating binary sensor: %s", str(e))
