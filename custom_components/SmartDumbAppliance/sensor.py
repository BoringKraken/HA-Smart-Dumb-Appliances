import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.event import track_state_change
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Smart Dumb Appliance sensor through config entry."""
    # Get data from the configuration entry
    entry_data = config_entry.data
    name = entry_data["name"]

    # Create and add the entities
    appliance_sensor = ApplianceSensor(hass, entry_data)
    async_add_entities([appliance_sensor], update_before_add=True)


class ApplianceSensor(SensorEntity):
    def __init__(self, hass, appliance):
        self._hass = hass
        
        # Initialize properties from configuration
        self._name = appliance["name"]
        self._entity_id = appliance["sensor_entity_id"]
        self._dead_zone = appliance["dead_zone"]
        self._debounce_time = appliance["debounce_time"]
        self._cost_helper_entity_id = appliance['cost_helper_entity_id']  # Referenced cost entity
        self._service_reminder = appliance["service_reminder"]
        
        self._state = "idle"
        self._active = False
        self._start_time = None
        self._energy_used = 0

        # Track changes in the sensor state
        track_state_change(hass, self._entity_id, self._state_changed)

    @property
    def _cost_per_kwh(self):
        """Retrieve cost per kWh from the input number helper entity."""
        try:
            return float(self._hass.states.get(self._cost_helper_entity_id).state)
        except (TypeError, ValueError, AttributeError):
            _LOGGER.error("Could not retrieve cost per kWh from %s", self._cost_helper_entity_id)
            return 0.0  # Default if error

    def _state_changed(self, entity, old_state, new_state):
        """Handle changes to the sensor's energy state."""
        try:
            new_value = float(new_state.state)

            if self._active:
                # Check if appliance should be considered 'off'
                if new_value <= self._dead_zone:
                    self._hass.loop.call_later(self._debounce_time, self._end_usage)
                else:
                    energy_increment = (new_value - self._dead_zone)
                    self._energy_used += energy_increment
            else:
                # Detect when appliance is turned 'on'
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
        return ENERGY_KILO_WATT_HOUR

    @property
    def state(self):
        """Return the state of the sensor."""
        return "Running" if self._active else "Idle"

    @property
    def icon(self):
        """Return the icon for the sensor."""
        if "washing machine" in self._name.lower():
            return "mdi:washing-machine"
        elif "dishwasher" in self._name.lower():
            return "mdi:dishwasher"
        else:
            return "mdi:power-plug"
