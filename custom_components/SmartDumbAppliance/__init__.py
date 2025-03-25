import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smart Dumb Appliance Integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Dumb Appliance from a config entry."""

    # Store a reference to the configuration entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    # Forward setup to platform
    hass.config_entries.async_setup_platforms(entry, ["sensor"])

    _LOGGER.debug("Entry setup: %s", entry.data)
    return True
