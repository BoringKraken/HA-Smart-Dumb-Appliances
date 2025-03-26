import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up Smart Dumb Appliance sensors through config entry."""
    # Extract the list of device-specific configurations from the entry data
    entry_data_list = config_entry.data.get("devices", [])
    _LOGGER.debug("Config entry data received: %s", entry_data_list)
    
    sensors = []

    for entry_data in entry_data_list:
        _LOGGER.debug("Processing device data: %s", entry_data)
        # Create a new sensor entity for each device entry in the list
        appliance_sensor = ApplianceSensor(hass, entry_data)
        _LOGGER.debug("Created appliance sensor: %s", appliance_sensor)
        sensors.append(appliance_sensor)
    
    # Add all sensors to Home Assistant entities
    async_add_entities(sensors, update_before_add=True)

class ApplianceSensor(SensorEntity):
    """Representation of a sensor for monitoring appliance state."""

    def __init__(self, hass, entry_data):
        """Initialize the appliance sensor."""
        self._hass = hass
        self._entry_data = entry_data
        self._name = entry_data.get("name", "Unknown Appliance")
        self._state = "idle"
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
        self._extra_attributes.update(
            {"last_updated": datetime.utcnow().isoformat()}
        )
