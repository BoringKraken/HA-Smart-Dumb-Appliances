import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up Smart Dumb Appliance sensors through config entry."""
    entry_data_list = config_entry.data.get("devices", [])
    _LOGGER.debug("Config entry data received: %s", entry_data_list)
    
    sensors = []

    for entry_data in entry_data_list:
        _LOGGER.debug("Processing device data: %s", entry_data)
        # Creating a sensor for each device entry
        appliance_sensor = ApplianceSensor(hass, entry_data)
        _LOGGER.debug("Created appliance sensor: %s", appliance_sensor)
        sensors.append(appliance_sensor)
    
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
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{self._entry_data.get('name')}_sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return self._extra_attributes

    @property
    def device_info(self):
        """Return device info for this entity."""
        return {
            "identifiers": {(self._hass.components.smart_dumb_appliance.DOMAIN, self.unique_id)},
            "name": self._name,
            "manufacturer": "HA Smart Dumb Appliance",
            "model": self._entry_data.get('model', 'Model XYZ'),
            "sw_version": self._entry_data.get('sw_version', '1.0'),
            "area_id": self._entry_data.get('area_id'),  # Example of setting a custom area
            "via_device": (self._hass.components.smart_dumb_appliance.DOMAIN, self._entry_data.get('via_device'))
        }

    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._extra_attributes.update({"last_updated": datetime.utcnow().isoformat()})
