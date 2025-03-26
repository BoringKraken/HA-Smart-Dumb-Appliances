import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

# Define logger for the module
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Smart Dumb Appliance sensor through config entry."""
    entry_data = config_entry.data
    _LOGGER.debug("Setting up Smart Dumb Appliance sensor with entry: %s", entry_data)

    if entry_data:
        # Initialize the sensor with the provided configuration data
        appliance_sensor = ApplianceSensor(hass, entry_data)
        # Add the prepared sensor to Home Assistant entities
        async_add_entities([appliance_sensor], update_before_add=True)
        _LOGGER.debug("Appliance sensor added: %s", appliance_sensor.name)
    else:
        # Log error if the config entry is empty or malformed
        _LOGGER.error("No entry data found for Smart Dumb Appliance sensor")

class ApplianceSensor(SensorEntity):
    """Representation of a Smart Dumb Appliance."""

    def __init__(self, hass: HomeAssistant, appliance):
        """Initialize the appliance sensor with configuration."""
        self._hass = hass        
        self._name = appliance["name"]
        self._entity_id = appliance["sensor_entity_id"]
        self._dead_zone = appliance["dead_zone"]
        self._debounce_time = appliance["debounce_time"]
        self._cost_helper_entity_id = appliance["cost_helper_entity_id"]
        self._service_reminder = appliance["service_reminder"]

        # Internal states for tracking usage
        self._state = "idle"
        self._active = False
        self._start_time = None
        self._energy_used = 0

    async def async_added_to_hass(self):
        """Register asynchronous state change handler once entity is added to Home Assistant."""
        _LOGGER.debug("Entity added to Home Assistant: %s", self.name)
        async_track_state_change_event(self._hass, [self._entity_id], self._async_state_changed)

    @property
    def _cost_per_kwh(self):
        """Retrieve cost per kWh using helper entity."""
        try:
            return float(self._hass.states.get(self._cost_helper_entity_id).state)
        except (TypeError, ValueError, AttributeError):
            _LOGGER.error("Could not retrieve cost per kWh from %s", self._cost_helper_entity_id)
            return 0.0  # Fallback cost if retrieval fails

    @callback
    async def _async_state_changed(self, event):
        """Handle changes to the sensor's monitored state asynchronously."""
        try:
            new_state = event.data.get('new_state')
            new_value = float(new_state.state)

            if self._active:
                # If appliance is active, check if it should stop
                if new_value <= self._dead_zone:
                    self._hass.loop.call_later(self._debounce_time, self._end_usage)
                else:
                    # Increment energy usage while active
                    energy_increment = (new_value - self._dead_zone)
                    self._energy_used += energy_increment
            else:
                # If appliance is not active, start it if conditions met
                if new_value > self._dead_zone:
                    self._start_usage()
        except ValueError as e:
            _LOGGER.error("Error processing state change: %s", e)

    def _start_usage(self):
        """Begin tracking the appliance usage."""
        self._start_time = self._hass.util.dt.now()
        self._active = True
        _LOGGER.info("%s started", self._name)

    def _end_usage(self):
        """Log the usage session and reset tracking states."""
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
        """Return the unit of measurement of energy used."""
        return "kWh"

    @property
    def state(self):
        """Return the current state of the appliance."""
        return "Running" if self._active else "Idle"

    @property
    def device_class(self):
        """Declare the sensor belongs to the energy device class."""
        return "energy"

    @property
    def icon(self):
        """Define an icon representing the appliance based on its type."""
        if "washing machine" in self._name.lower():
            return "mdi:washing-machine"
        elif "dishwasher" in self._name.lower():
            return "mdi:dishwasher"
        else:
            return "mdi:power-plug"
