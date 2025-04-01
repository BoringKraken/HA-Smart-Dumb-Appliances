"""Data coordinator for Smart Dumb Appliance."""
from dataclasses import dataclass
import logging
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

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

            # Determine if the appliance is running
            is_on = current_power > self._start_watts or (self._was_on and current_power > self._stop_watts)
            
            # Track state changes
            if is_on and not self._was_on:
                self._start_time = last_update
                self._end_time = None
                _LOGGER.debug(
                    "Appliance turned on (current: %.1fW, start: %.1fW)",
                    current_power,
                    self._start_watts
                )
            elif not is_on and self._was_on:
                self._end_time = last_update
                self._use_count += 1
                _LOGGER.debug(
                    "Appliance turned off (current: %.1fW, stop: %.1fW, Duration: %s, Total uses: %d)",
                    current_power,
                    self._stop_watts,
                    self._end_time - self._start_time if self._start_time else "unknown",
                    self._use_count
                )
            
            self._was_on = is_on

            # Calculate cycle energy (if we have timing data)
            if self._start_time and is_on:
                duration = (last_update - self._start_time).total_seconds() / 3600  # Convert to hours
                self._cycle_energy = (current_power * duration) / 1000  # Convert to kWh

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

            # Log the update
            _LOGGER.debug(
                "Coordinator updated: %.1fW (running: %s, use count: %d, cycle energy: %.3f kWh)",
                current_power,
                is_on,
                self._use_count,
                self._cycle_energy
            )

            return data

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error reading power sensor %s: %s", self._power_sensor, err)
            raise UpdateFailed(f"Error reading power sensor: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error updating data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err 