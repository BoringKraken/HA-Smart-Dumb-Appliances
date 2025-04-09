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

from .const import (
    DOMAIN,
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEBOUNCE,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEBOUNCE,
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
    _LOGGER.info("Setting up entry: %s", entry.entry_id)
    
    # Verify required configuration
    if not entry.data.get(CONF_POWER_SENSOR):
        _LOGGER.error("Required power sensor not configured for entry: %s", entry.entry_id)
        return False
    
    # Create the coordinator
    coordinator = SmartDumbApplianceCoordinator(hass, entry)
    
    # Store the coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up the coordinator
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()
    
    # Set up the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading entry: %s", entry.entry_id)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    
    return unload_ok
