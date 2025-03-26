"""
Implements sensor entities for Smart Dumb Appliance.
Example: A cost sensor that calculates cost by multiplying usage * cost/kWh.
"""

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE

from .const import DOMAIN, CONF_POWER_SENSOR, CONF_COST_SENSOR, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Smart Dumb Appliance sensors from a ConfigEntry."""
    config = hass.data[DOMAIN][entry.entry_id]
    device_name = config.get(CONF_DEVICE_NAME, "Appliance")
    power_sensor_id = config.get(CONF_POWER_SENSOR)
    cost_sensor_id = config.get(CONF_COST_SENSOR)

    sensors = []
    if cost_sensor_id:
        sensors.append(
            SmartDumbApplianceCostSensor(
                entry_id=entry.entry_id,
                name=f"{device_name} Cost",
                power_sensor_entity_id=power_sensor_id,
                cost_sensor_entity_id=cost_sensor_id,
            )
        )

    async_add_entities(sensors, update_before_add=True)

class SmartDumbApplianceCostSensor(SensorEntity):
    """A sensor that computes cost from a power sensor and a cost-per-kWh sensor."""

    def __init__(self, entry_id, name, power_sensor_entity_id, cost_sensor_entity_id):
        self._entry_id = entry_id
        self._name = name
        self._power_sensor_entity_id = power_sensor_entity_id
        self._cost_sensor_entity_id = cost_sensor_entity_id
        self._state = None
        self._attr_unique_id = f"{entry_id}_cost_sensor"

    @property
    def name(self):
        """Name shown in the UI."""
        return self._name

    @property
    def native_value(self):
        """The calculated cost."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return a suitable currency symbol or code."""
        return "USD"

    @property
    def should_poll(self):
        """We'll poll the state machine for updates."""
        return True

    async def async_update(self):
        """Fetch usage and cost, then calculate total cost."""
        power_state_obj = self.hass.states.get(self._power_sensor_entity_id)
        cost_state_obj = self.hass.states.get(self._cost_sensor_entity_id)

        if not power_state_obj or power_state_obj.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            usage_kwh = 0
        else:
            try:
                usage_kwh = float(power_state_obj.state)
            except ValueError:
                usage_kwh = 0

        if not cost_state_obj or cost_state_obj.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            cost_per_kwh = 0
        else:
            try:
                cost_per_kwh = float(cost_state_obj.state)
            except ValueError:
                cost_per_kwh = 0

        self._state = usage_kwh * cost_per_kwh
