from homeassistant.core import HomeAssistant
from .const import DOMAIN  # Import the domain from the constants

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the integration from configuration.yaml if needed."""
    hass.data.setdefault(DOMAIN, {})  # Initialize domain data storage
    return True  # Return True to indicate successful setup

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up the smart dumb appliance from a config entry."""
    # Store entry data in Home Assistant's domain-specific data storage
    hass.data[DOMAIN][entry.entry_id] = entry.data
    return True  # Return True to indicate successful entry setup

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    # Remove entry data from Home Assistant's domain-specific storage
    hass.data[DOMAIN].pop(entry.entry_id)
    return True  # Return True to indicate successful entry unload
