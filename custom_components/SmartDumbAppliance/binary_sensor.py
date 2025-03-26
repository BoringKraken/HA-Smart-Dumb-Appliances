"""
Binary Sensor for Smart Dumb Appliance.
A simple example: 'Running' if usage is above a threshold, off if below
for a certain debounce period.
"""

import logging
import time
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE

from .const import DOMAIN, CONF_POWER_SENSOR, CONF_DEAD_ZONE, CONF_DEBOUNCE, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the binary sensor from a ConfigEntry."""
    config = hass.data[DOMAIN][entry.entry_id]
    device_name = config.get(CONF_DEVICE_NAME, "Appliance")
    power_sensor_id = config.get(CONF_POWER_SENSOR)
    dead_zone = config.get(CONF_DEAD_ZONE, 5)
    debounce = config.get(CONF_DEBOUNCE, 30)

    sensor = SmartDumbApplianceBinarySensor(
        entry_id=entry.entry_id,
        name=f"{device_name} Running",
        power_sensor_entity_id=power_sensor_id,
        dead_zone=dead_zone,
        debounce=debounce
    )

    async_add_entities([sensor], update_before_add=True)

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """Binary Sensor: ON if above threshold, OFF if below threshold for > debounce time."""

    def __init__(self, entry_id, name, power_sensor_entity_id, dead_zone, debounce):
        self._entry_id = entry_id
        self._name = name
        self._power_sensor_entity_id = power_sensor_entity_id
        self._dead_zone = float(dead_zone)
        self._debounce = float(debounce)

        self._state = False
        self._last_above_threshold = 0
        self._attr_unique_id = f"{entry_id}_running_binary"

    @property
    def name(self):
        """Human-readable name."""
        return self._name

    @property
    def is_on(self):
        """Return whether the appliance is considered running."""
        return self._state

    @property
    def should_poll(self):
        """Enable polling for demonstration."""
        return True

    async def async_update(self):
        """Check power usage and update ON/OFF state with dead zone and debounce."""
        power_state_obj = self.hass.states.get(self._power_sensor_entity_id)
        if not power_state_obj or power_state_obj.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return

        try:
            usage = float(power_state_obj.state)
        except ValueError:
            usage = 0

        if usage > self._dead_zone:
            self._last_above_threshold = time.time()
            self._state = True
        else:
            if (time.time() - self._last_above_threshold) > self._debounce:
                self._state = False
