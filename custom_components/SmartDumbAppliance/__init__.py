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

# Debug log to verify module loading
_LOGGER.info("Smart Dumb Appliance integration is being loaded")

# Define the platforms that this integration supports
PLATFORMS = ["sensor", "binary_sensor"]

async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Smart Dumb Appliance integration."""
    _LOGGER.info("Setting up Smart Dumb Appliance integration")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Dumb Appliance from a ConfigEntry."""
    _LOGGER.debug("Setting up Smart Dumb Appliance, entry_id: %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Smart Dumb Appliance ConfigEntry."""
    _LOGGER.debug("Unloading Smart Dumb Appliance, entry_id: %s", entry.entry_id)

    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
