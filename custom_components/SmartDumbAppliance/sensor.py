"""Sensor platform for Smart Dumb Appliance."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SmartDumbApplianceCoordinator
from .service_sensor import SmartDumbApplianceServiceSensor
from .power_sensor import SmartDumbAppliancePowerSensor
from .duration_sensor import SmartDumbApplianceDurationSensor
from .energy_sensor import SmartDumbApplianceEnergySensor
from .cost_sensor import SmartDumbApplianceCostSensor

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create all sensor entities
    sensors = [
        SmartDumbApplianceServiceSensor(coordinator, config_entry),
        SmartDumbAppliancePowerSensor(coordinator, config_entry),
        SmartDumbApplianceDurationSensor(coordinator, config_entry),
        SmartDumbApplianceEnergySensor(coordinator, config_entry),
        SmartDumbApplianceCostSensor(coordinator, config_entry),
    ]
    
    # Add all sensors to Home Assistant
    async_add_entities(sensors)
    
    _LOGGER.debug("Added %d sensors for %s", len(sensors), config_entry.title) 