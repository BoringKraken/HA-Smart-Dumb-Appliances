"""Data coordinator for Smart Dumb Appliance."""
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.core import callback

from .const import (
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
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
    power_state: float  # Current power in watts
    power_kw: float    # Current power in kilowatts
    is_running: bool
    start_time: datetime | None
    end_time: datetime | None
    use_count: int
    cycle_energy: float  # Energy used in current cycle (kWh)
    previous_cycle_energy: float  # Energy used in previous cycle (kWh)
    total_energy: float  # Total energy used (kWh)
    cycle_cost: float   # Cost of current cycle
    previous_cycle_cost: float  # Cost of previous cycle
    total_cost: float   # Total cost
    last_power: float   # Previous power reading for trapezoidal integration
    last_power_time: datetime | None  # Timestamp of previous power reading
    cycle_duration: timedelta | None  # Duration of current or last completed cycle
    last_cycle_duration: timedelta | None  # Duration of previous cycle
    total_duration: timedelta  # Total duration of all cycles
    service_status: str  # Current service status (ok/needs_service/disabled)
    service_reminder_enabled: bool  # Whether service reminders are enabled
    service_reminder_message: str  # Message to display when service is needed
    service_reminder_count: int  # Number of cycles until service is needed
    remaining_cycles: int  # Number of cycles remaining until service is needed

class SmartDumbApplianceCoordinator(DataUpdateCoordinator):
    """Coordinator for Smart Dumb Appliance data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{config_entry.data.get('name', 'Smart Dumb Appliance')}_coordinator",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=30),  # Poll every 30 seconds as backup
        )
        
        self.config_entry = config_entry
        self._power_sensor = config_entry.data[CONF_POWER_SENSOR]
        self._cost_sensor = config_entry.data.get(CONF_COST_SENSOR)
        self._start_watts = config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS)
        self._stop_watts = config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)
        
        # Initialize state tracking
        self._start_time = None
        self._end_time = None
        self._use_count = 0
        self._cycle_energy = 0.0
        self._previous_cycle_energy = 0.0
        self._total_energy = 0.0
        self._cycle_cost = 0.0
        self._previous_cycle_cost = 0.0
        self._total_cost = 0.0
        self._was_on = False
        self._last_power = 0.0
        self._last_power_time = None
        self._last_cycle_end_time = None
        self._total_duration = timedelta(0)
        self.data = None

        # Store the unsubscribe callback
        self._unsubscribe = None

    def _calculate_interval_energy(self, current_power: float, current_time: datetime) -> float:
        """
        Calculate energy used in the interval using trapezoidal integration.
        
        Args:
            current_power: Current power reading in watts
            current_time: Current timestamp
            
        Returns:
            float: Energy used in the interval in kWh
        """
        if self._last_power_time is None:
            self._last_power = current_power
            self._last_power_time = current_time
            return 0.0
            
        # Calculate time difference in hours
        time_diff = (current_time - self._last_power_time).total_seconds() / 3600
        
        # Use trapezoidal integration: area = (a + b)h/2
        # Convert watts to kilowatts by dividing by 1000
        interval_energy = (self._last_power + current_power) * time_diff / (2 * 1000)
        
        # Update last values for next calculation
        self._last_power = current_power
        self._last_power_time = current_time
        
        return interval_energy

    def _get_current_cost_rate(self) -> Optional[float]:
        """Get the current cost per kWh from the cost sensor."""
        if not self._cost_sensor:
            return None
            
        cost_state = self.hass.states.get(self._cost_sensor)
        if cost_state is None:
            _LOGGER.warning("Cost sensor %s not found", self._cost_sensor)
            return None
            
        try:
            return float(cost_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid cost sensor state: %s", cost_state.state)
            return None

    async def _async_update_data(self) -> ApplianceData:
        """Fetch data from the power sensor."""
        try:
            # Get current power reading
            power_state = self.hass.states.get(self._power_sensor)
            if power_state is None:
                _LOGGER.warning("Power sensor %s not found", self._power_sensor)
                raise UpdateFailed("Power sensor not found")

            current_power = float(power_state.state)
            current_time = dt_util.utcnow()
            power_kw = current_power / 1000  # Convert to kilowatts

            # Calculate energy used in this interval
            interval_energy = self._calculate_interval_energy(current_power, current_time)
            
            # Get current cost rate
            cost_rate = self._get_current_cost_rate()
            
            # Calculate interval cost if we have a rate
            interval_cost = interval_energy * cost_rate if cost_rate is not None else 0.0

            # Log current state
            _LOGGER.debug(
                "Current state - Power: %.1fW (%.3f kW), Interval energy: %.3f kWh, Cost rate: %s/kWh",
                current_power,
                power_kw,
                interval_energy,
                f"${cost_rate:.4f}" if cost_rate is not None else "unknown"
            )

            # Determine if the appliance is running
            is_on = current_power > self._start_watts or (self._was_on and current_power > self._stop_watts)
            
            # Calculate current duration
            current_duration = current_time - self._start_time if self._start_time else timedelta(0)
            
            # Track state changes
            if is_on and not self._was_on:
                self._start_time = current_time
                self._end_time = None
                self._cycle_energy = 0.0
                self._cycle_cost = 0.0
                _LOGGER.debug(
                    "Appliance turned on - Current: %.1fW (%.3f kW), Start threshold: %.1fW",
                    current_power,
                    power_kw,
                    self._start_watts
                )
            elif not is_on and self._was_on:
                self._end_time = current_time
                self._use_count += 1
                
                # Store previous cycle values when a cycle ends
                if self._last_cycle_end_time != self._end_time:
                    self._previous_cycle_energy = self._cycle_energy
                    self._previous_cycle_cost = self._cycle_cost
                    self._last_cycle_end_time = self._end_time
                    _LOGGER.debug(
                        "Cycle ended - Previous cycle energy: %.3f kWh, cost: $%.2f",
                        self._previous_cycle_energy,
                        self._previous_cycle_cost
                    )
                
                _LOGGER.debug(
                    "Appliance turned off - Duration: %s, Cycle energy: %.3f kWh, Cycle cost: $%.2f",
                    current_duration,
                    self._cycle_energy,
                    self._cycle_cost
                )
            
            # Update energy and cost tracking
            if is_on or self._was_on:  # Track energy while running and for the final interval when turning off
                self._cycle_energy += interval_energy
                self._total_energy += interval_energy
                self._cycle_cost += interval_cost
                self._total_cost += interval_cost
            
            self._was_on = is_on

            # Create and return the data object
            data = ApplianceData(
                last_update=current_time,
                power_state=current_power,
                power_kw=power_kw,
                is_running=is_on,
                start_time=self._start_time,
                end_time=self._end_time,
                use_count=self._use_count,
                cycle_energy=self._cycle_energy,
                previous_cycle_energy=self._previous_cycle_energy,
                total_energy=self._total_energy,
                cycle_cost=self._cycle_cost,
                previous_cycle_cost=self._previous_cycle_cost,
                total_cost=self._total_cost,
                last_power=self._last_power,
                last_power_time=self._last_power_time,
                cycle_duration=current_duration if is_on else None,
                last_cycle_duration=current_duration if not is_on else None,
                total_duration=self._total_duration + current_duration,
                service_status="ok" if is_on else "disabled",
                service_reminder_enabled=False,
                service_reminder_message="",
                service_reminder_count=0,
                remaining_cycles=0
            )
            
            _LOGGER.debug(
                "Generated new data - Power: %.1fW (%.3f kW), Running: %s, Cycle energy: %.3f kWh, "
                "Previous cycle energy: %.3f kWh, Total energy: %.3f kWh, Cycle cost: $%.2f, "
                "Previous cycle cost: $%.2f, Total cost: $%.2f",
                current_power,
                power_kw,
                is_on,
                self._cycle_energy,
                self._previous_cycle_energy,
                self._total_energy,
                self._cycle_cost,
                self._previous_cycle_cost,
                self._total_cost
            )
            
            return data

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error reading power sensor %s: %s", self._power_sensor, err)
            raise UpdateFailed(f"Error reading power sensor: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error updating data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Start the periodic updates
        await self.async_config_entry_first_refresh()
        
        # Set up power sensor state tracking
        self._unsubscribe = self.hass.helpers.event.async_track_state_change(
            self._power_sensor,
            self._async_power_sensor_changed
        )

    async def async_shutdown(self) -> None:
        """Clean up resources."""
        if self._unsubscribe:
            self._unsubscribe()
        await super().async_shutdown()

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
        
        # Schedule an update
        self.hass.async_create_task(self.async_refresh())

    async def _async_handle_power_change(self) -> None:
        """Handle power sensor changes asynchronously."""
        try:
            data = await self._async_update_data()
            self.data = data
            _LOGGER.debug("Updated coordinator data: %s", data)
            self.async_set_updated_data(data)
        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            self.last_update_success = False
            self.async_update_listeners()

    async def async_update_data(self) -> ApplianceData:
        """
        Fetch data from the power sensor.
        
        This is the update method for the coordinator. It will be called
        periodically to update the sensor data.
        
        Returns:
            ApplianceData: The updated appliance data
        """
        return await self._async_update_data() 