import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Smart Dumb Appliance sensor through config entry."""
    # Get data from the configuration entry
    entry_data = config_entry.data

    # Create and add the entities
    appliance_sensor = ApplianceSensor(hass, entry_data)
    async_add_entities([appliance_sensor], update_before_add=True)


class ApplianceSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, appliance):
        self._hass = hass        
        self._name = appliance["name"]
        self._entity_id = appliance["sensor_entity_id"]
        self._dead_zone = appliance["dead_zone"]
        self._debounce_time = appliance["debounce_time"]
        self._cost_helper_entity_id = appliance["cost_helper_entity_id"]
        self._service_reminder = appliance["service_reminder"]
        
        self._state = "idle"
        self._active = False
        self._start_time = None
        self._energy_used = 0

    async def async_added_to_hass(self):
        """Register asynchronous state change handler."""
        async_track_state_change_event(self._hass, [self._entity_id], self._async_state_changed)

    @property
    def _cost_per_kwh(self):
        """Retrieve cost per kWh from input number helper entity."""
        try:
            return float(self._hass.states.get(self._cost_helper_entity_id).state)
        except (TypeError, ValueError, AttributeError):
            _LOGGER.error("Could not retrieve cost per kWh from %s", self._cost_helper_entity_id)
            return 0.0  # Default if retrieval fails

    @callback
    async def _async_state_changed(self, event):
        """Handle changes to the sensor's energy state asynchronously."""
        try:
            new_state = event.data.get('new_state')
            new_value = float(new_state.state)

            if self._active:
                if new_value <= self._dead_zone:
                    self._hass.loop.call_later(self._debounce_time, self._end_usage)
                else:
                    energy_increment = (new_value - self._dead_zone)
                    self._energy_used += energy_increment
            else:
                if new_value > self._dead_zone:
                    self._start_usage()
        except ValueError as e:
            _LOGGER.error("Error processing state change: %s", e)

    def _start_usage(self):
        """Mark the appliance as active and start timing."""
        self._start_time = self._hass.util.dt.now()
        self._active = True
        _LOGGER.info("%s started", self._name)

    def _end_usage(self):
        """Log usage information and reset states."""
        elapsed_time = self._hass.util.dt.now() - self._start_time
        _LOGGER.info("%s finished: duration %s, energy used %.2f kWh, cost %.2f", 
                    self._name, elapsed_time, self._energy_used, self._energy_used * self._cost_per_kwh)
        self._active = False
        self._energy_used = 0

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "kWh"

    @property
    def state(self):
        """Return the state of the sensor."""
        return "Running" if self._active else "Idle"

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return "energy"

    @property
    def icon(self):
        """Return the icon for the sensor."""
        if "washing machine" in self._name.lower():
            return "mdi:washing-machine"
        elif "dishwasher" in self._name.lower():
            return "mdi:dishwasher"
        else:
            return "mdi:power-plug"
