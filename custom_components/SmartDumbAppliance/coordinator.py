"""Data coordinator for Smart Dumb Appliance."""
from dataclasses import dataclass
import logging
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.core import callback

from .const import (
    CONF_POWER_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
)

_LOGGER = logging.getLogger(__name__)

@dataclass
class ApplianceData:
    """Class to hold appliance data."""
    last_update: datetime
    power_state: float
    is_running: bool
    start_time: datetime | None
    end_time: datetime | None
    use_count: int
    cycle_energy: float
    cycle_cost: float

class SmartDumbApplianceCoordinator(DataUpdateCoordinator):
    """Coordinator for Smart Dumb Appliance data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{config_entry.data.get('name', 'Smart Dumb Appliance')}_coordinator",
            update_method=self.async_update_data,
            update_interval=None,  # We'll update based on power sensor changes
        )
        
        self.config_entry = config_entry
        self._power_sensor = config_entry.data[CONF_POWER_SENSOR]
        self._start_watts = config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS)
        self._stop_watts = config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)
        
        # Initialize state tracking
        self._start_time = None
        self._end_time = None
        self._use_count = 0
        self._cycle_energy = 0.0
        self._cycle_cost = 0.0
        self._was_on = False

        # Subscribe to power sensor changes
        self.async_on_remove(
            self.hass.helpers.event.async_track_state_change(
                self._power_sensor,
                self._async_power_sensor_changed
            )
        )

    @callback
    def _async_power_sensor_changed(self, entity_id: str, old_state: Any, new_state: Any) -> None:
        """Handle power sensor state changes."""
        if new_state is None:
            _LOGGER.debug("Power sensor %s state is None, skipping update", entity_id)
            return
        
        _LOGGER.debug(
            "Power sensor %s changed: old_state=%s, new_state=%s",
            entity_id,
            old_state.state if old_state else "None",
            new_state.state
        )
        self.async_set_updated_data(self.async_update_data())

    async def async_update_data(self) -> ApplianceData:
        """
        Fetch data from the power sensor.
        
        This is the update method for the coordinator. It will be called
        periodically to update the sensor data.
        
        Returns:
            ApplianceData: The updated appliance data
        """
        try:
            # Get current power reading
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                raise UpdateFailed("Power sensor not found")

            current_power = float(power_state.state)
            last_update = dt_util.utcnow()

            # Log all current state information
            _LOGGER.debug(
                "Current state - Power: %.1fW, Start threshold: %.1fW, Stop threshold: %.1fW, "
                "Was on: %s, Start time: %s, End time: %s, Use count: %d, Cycle energy: %.3f kWh",
                current_power,
                self._start_watts,
                self._stop_watts,
                self._was_on,
                self._start_time,
                self._end_time,
                self._use_count,
                self._cycle_energy
            )

            # Determine if the appliance is running
            is_on = current_power > self._start_watts or (self._was_on and current_power > self._stop_watts)
            
            # Track state changes
            if is_on and not self._was_on:
                self._start_time = last_update
                self._end_time = None
                _LOGGER.debug(
                    "Appliance turned on - Current: %.1fW, Start threshold: %.1fW, Start time: %s",
                    current_power,
                    self._start_watts,
                    self._start_time
                )
            elif not is_on and self._was_on:
                self._end_time = last_update
                self._use_count += 1
                duration = self._end_time - self._start_time if self._start_time else "unknown"
                _LOGGER.debug(
                    "Appliance turned off - Current: %.1fW, Stop threshold: %.1fW, "
                    "Duration: %s, Total uses: %d, End time: %s",
                    current_power,
                    self._stop_watts,
                    duration,
                    self._use_count,
                    self._end_time
                )
            
            self._was_on = is_on

            # Calculate cycle energy (if we have timing data)
            if self._start_time and is_on:
                duration = (last_update - self._start_time).total_seconds() / 3600  # Convert to hours
                self._cycle_energy = (current_power * duration) / 1000  # Convert to kWh
                _LOGGER.debug(
                    "Cycle energy updated - Duration: %.2f hours, Power: %.1fW, Energy: %.3f kWh",
                    duration,
                    current_power,
                    self._cycle_energy
                )

            # Create and return the data object
            data = ApplianceData(
                last_update=last_update,
                power_state=current_power,
                is_running=is_on,
                start_time=self._start_time,
                end_time=self._end_time,
                use_count=self._use_count,
                cycle_energy=self._cycle_energy,
                cycle_cost=self._cycle_cost,
            )

            # Log the final update
            _LOGGER.debug(
                "Coordinator update complete - Power: %.1fW, Running: %s, Use count: %d, "
                "Cycle energy: %.3f kWh, Last update: %s",
                current_power,
                is_on,
                self._use_count,
                self._cycle_energy,
                last_update
            )

            return data

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error reading power sensor %s: %s", self._power_sensor, err)
            raise UpdateFailed(f"Error reading power sensor: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error updating data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err 