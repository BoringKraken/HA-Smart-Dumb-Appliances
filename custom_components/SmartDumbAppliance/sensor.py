"""
Sensor implementation for Smart Dumb Appliance.
This module provides sensors that calculate various metrics for monitored appliances,
such as operating costs based on power consumption and energy rates.
"""

import logging
from typing import Optional
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_DEVICE_NAME,
    ATTR_POWER_USAGE,
    ATTR_TOTAL_COST,
    ATTR_LAST_UPDATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """
    Set up Smart Dumb Appliance sensors from a ConfigEntry.
    
    Args:
        hass: The Home Assistant instance
        entry: The ConfigEntry containing the configuration
        async_add_entities: Callback to add entities to Home Assistant
    """
    try:
        config = hass.data[DOMAIN][entry.entry_id]
        device_name = config.get(CONF_DEVICE_NAME, "Appliance")
        power_sensor_id = config.get(CONF_POWER_SENSOR)
        cost_sensor_id = config.get(CONF_COST_SENSOR)

        if not power_sensor_id:
            _LOGGER.error("No power sensor specified for %s", device_name)
            return

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

        if sensors:
            async_add_entities(sensors, update_before_add=True)
            _LOGGER.debug("Successfully set up %d sensors for %s", len(sensors), device_name)
        else:
            _LOGGER.warning("No sensors configured for %s", device_name)
            
    except Exception as e:
        _LOGGER.error("Error setting up sensors: %s", str(e))

class SmartDumbApplianceCostSensor(SensorEntity):
    """
    Sensor that calculates the operating cost of an appliance.
    
    This sensor computes the cost of operation by multiplying the power consumption
    by the current energy rate. It updates whenever either the power consumption
    or energy rate changes.
    """

    def __init__(
        self,
        entry_id: str,
        name: str,
        power_sensor_entity_id: str,
        cost_sensor_entity_id: str,
    ):
        """
        Initialize the cost sensor.
        
        Args:
            entry_id: The unique identifier for this configuration entry
            name: The display name for the sensor
            power_sensor_entity_id: The entity ID of the power consumption sensor
            cost_sensor_entity_id: The entity ID of the cost per kWh sensor
        """
        self._entry_id = entry_id
        self._name = name
        self._power_sensor_entity_id = power_sensor_entity_id
        self._cost_sensor_entity_id = cost_sensor_entity_id
        self._state: Optional[float] = None
        self._attr_unique_id = f"{entry_id}_cost_sensor"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self) -> Optional[float]:
        """Return the calculated cost."""
        return self._state

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement for the cost."""
        return "USD"

    @property
    def should_poll(self) -> bool:
        """Return True to enable polling for updates."""
        return True

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            ATTR_POWER_USAGE: self._get_power_usage(),
            ATTR_TOTAL_COST: self._state,
            ATTR_LAST_UPDATE: self.hass.states.get(self._power_sensor_entity_id).last_updated
        }

    def _get_power_usage(self) -> Optional[float]:
        """Get the current power usage from the power sensor."""
        try:
            power_state = self.hass.states.get(self._power_sensor_entity_id)
            if power_state and power_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                return float(power_state.state)
        except (ValueError, TypeError) as e:
            _LOGGER.error("Invalid power value from sensor %s: %s", self._power_sensor_entity_id, str(e))
        return None

    def _get_cost_per_kwh(self) -> Optional[float]:
        """Get the current cost per kWh from the cost sensor."""
        try:
            cost_state = self.hass.states.get(self._cost_sensor_entity_id)
            if cost_state and cost_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                return float(cost_state.state)
        except (ValueError, TypeError) as e:
            _LOGGER.error("Invalid cost value from sensor %s: %s", self._cost_sensor_entity_id, str(e))
        return None

    async def async_update(self) -> None:
        """
        Update the sensor state by calculating the current cost.
        
        This method fetches the current power usage and energy rate, then calculates
        the total cost of operation.
        """
        try:
            power_usage = self._get_power_usage()
            cost_per_kwh = self._get_cost_per_kwh()

            if power_usage is not None and cost_per_kwh is not None:
                self._state = power_usage * cost_per_kwh
            else:
                self._state = None

        except Exception as e:
            _LOGGER.error("Error updating cost sensor: %s", str(e))
            self._state = None
