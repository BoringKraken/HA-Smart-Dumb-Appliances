"""
Integration initialization for the Smart Dumb Appliance.

This module handles the core setup and teardown of the Smart Dumb Appliance integration.
It manages the loading/unloading of configuration entries and forwards setup to the
sensor and binary_sensor platforms.

The integration provides functionality to monitor "dumb" appliances by tracking their
energy usage patterns and providing status information through Home Assistant.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEBOUNCE,
    CONF_START_DEBOUNCE,
    CONF_END_DEBOUNCE,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    CONF_DEVICE_NAME,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEBOUNCE,
    DEFAULT_START_DEBOUNCE,
    DEFAULT_END_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT,
)
from .coordinator import SmartDumbApplianceCoordinator

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

# Debug log to verify module loading
_LOGGER.info("Smart Dumb Appliance integration is being loaded")

# Define the platforms that this integration supports
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smart Dumb Appliance integration."""
    _LOGGER.info("Setting up Smart Dumb Appliance integration")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Dumb Appliance from a config entry."""
    # Get the configuration data
    config = entry.data
    
    # Handle migration from old debounce to new start/end debounce
    if CONF_DEBOUNCE in config and CONF_START_DEBOUNCE not in config:
        _LOGGER.info("Migrating from old debounce configuration to new start/end debounce")
        old_debounce = config[CONF_DEBOUNCE]
        config[CONF_START_DEBOUNCE] = old_debounce
        config[CONF_END_DEBOUNCE] = old_debounce
        # Update the config entry
        hass.config_entries.async_update_entry(entry, data=config)
    
    # Create the coordinator
    coordinator = SmartDumbApplianceCoordinator(hass, config)
    
    # Store the coordinator in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        _LOGGER.info("Unloading entry: %s", entry.data.get(CONF_DEVICE_NAME, entry.entry_id))
        
        # Get the coordinator
        coordinator = hass.data[DOMAIN].get(entry.entry_id)
        if not coordinator:
            _LOGGER.warning("No coordinator found for entry: %s", entry.entry_id)
            return True
            
        # Shutdown the coordinator first
        await coordinator.async_shutdown()
        
        # Unload all platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        if unload_ok:
            # Get the entity registry
            entity_registry = er.async_get(hass)
            device_registry = dr.async_get(hass)
            
            # Get the device
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, entry.entry_id)}
            )
            
            if device:
                # Update the device name
                device_registry.async_update_device(
                    device.id,
                    name=entry.data.get(CONF_DEVICE_NAME, "Smart Dumb Appliance")
                )
                
                # Update all entities associated with this device
                for entity in entity_registry.entities.values():
                    if entity.device_id == device.id:
                        # Update the entity name to match the new device name
                        new_name = f"{entry.data.get(CONF_DEVICE_NAME, 'Smart Dumb Appliance')} {entity.original_name.split(' ', 1)[1]}"
                        entity_registry.async_update_entity(
                            entity.entity_id,
                            name=new_name
                        )
                        _LOGGER.debug("Updated entity name: %s -> %s", entity.original_name, new_name)
            
            # Remove the coordinator from hass.data
            hass.data[DOMAIN].pop(entry.entry_id)
            
        return unload_ok
        
    except Exception as e:
        _LOGGER.error("Error unloading entry: %s", str(e))
        return False
