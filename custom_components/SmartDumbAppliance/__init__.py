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
    _LOGGER.info("Setting up entry: %s", entry.entry_id)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Smart Dumb Appliance ConfigEntry."""
    _LOGGER.info("Unloading entry: %s", entry.entry_id)
    return True
