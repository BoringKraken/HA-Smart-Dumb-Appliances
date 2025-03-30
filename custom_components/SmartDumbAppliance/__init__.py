"""
Integration initialization for the Smart Dumb Appliance.

This module handles the core setup and teardown of the Smart Dumb Appliance integration.
It manages the loading/unloading of configuration entries and forwards setup to the
sensor and binary_sensor platforms.

The integration provides functionality to monitor "dumb" appliances by tracking their
energy usage patterns and providing status information through Home Assistant.
"""

import logging
from typing import Any, Dict
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

# Define the platforms that this integration supports
PLATFORMS = ["sensor", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Smart Dumb Appliance from a ConfigEntry.
    
    Args:
        hass: The Home Assistant instance
        entry: The ConfigEntry containing the configuration data
        
    Returns:
        bool: True if setup was successful, False otherwise
    """
    try:
        _LOGGER.debug("Setting up Smart Dumb Appliance, entry_id: %s", entry.entry_id)
        
        # Initialize the domain data structure if it doesn't exist
        hass.data.setdefault(DOMAIN, {})
        
        # Store the configuration data for this entry
        hass.data[DOMAIN][entry.entry_id] = entry.data

        # Forward setup to all supported platforms
        for platform in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )
            
        return True
        
    except Exception as e:
        _LOGGER.error("Error setting up Smart Dumb Appliance: %s", str(e))
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload Smart Dumb Appliance ConfigEntry.
    
    Args:
        hass: The Home Assistant instance
        entry: The ConfigEntry to unload
        
    Returns:
        bool: True if unload was successful, False otherwise
    """
    try:
        _LOGGER.debug("Unloading Smart Dumb Appliance, entry_id: %s", entry.entry_id)

        # Forward unload to all platforms
        unload_ok = all(
            await hass.config_entries.async_forward_entry_unload(entry, platform)
            for platform in PLATFORMS
        )

        # Clean up the domain data if unload was successful
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id, None)
            _LOGGER.debug("Successfully unloaded Smart Dumb Appliance")

        return unload_ok
        
    except Exception as e:
        _LOGGER.error("Error unloading Smart Dumb Appliance: %s", str(e))
        return False
