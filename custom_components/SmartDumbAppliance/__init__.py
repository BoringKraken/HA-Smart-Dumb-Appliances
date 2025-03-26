"""
Integration initialization for the Smart Dumb Appliance.

Handles loading/unloading of config entries and forwarding setup
to the sensor/binary_sensor platforms.
"""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

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
