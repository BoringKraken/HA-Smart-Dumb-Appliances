from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up smart dumb appliance from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up smart dumb appliance from a config entry."""
    # Store entry data in Home Assistant's domain-specific data storage
    hass.data[DOMAIN][entry.entry_id] = entry.data
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    # Remove entry data from Home Assistant's domain-specific storage
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
