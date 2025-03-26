import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# Define logger for the module
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities) -> None:
    """Set up Smart Dumb Appliance sensor through config entry."""
    entry_data = config_entry.data
    _LOGGER.debug("Setting up Smart Dumb Appliance sensor with entry: %s", entry_data)

    if entry_data:
        # Initialize the sensor with the provided configuration data
        appliance_sensor = ApplianceSensor(hass, entry_data)
        # Add the prepared sensor to Home Assistant entities
        async_add_entities([appliance_sensor], update_before_add=True)

class ApplianceSensor(SensorEntity):
    """Representation of a sensor for monitoring appliance state."""

    def __init__(self, hass, entry_data):
        """Initialize the appliance sensor."""
        self._hass = hass
        self._entry_data = entry_data
        self._state = None
        self._name = entry_data.get("name", "Unknown Appliance")
        self._extra_attributes = {}

    @property
    def name(self):
        """Return the name of the appliance sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return self._extra_attributes

    async def async_update(self):
        """Fetch new state data for the sensor."""
        # Logic to update self._state and self._extra_attributes
        # Example static state, replace with dynamic logic
        self._state = "idle"  # This is an example, implement dynamic logic
        self._extra_attributes.update({"last_updated": self._hass.time()})
