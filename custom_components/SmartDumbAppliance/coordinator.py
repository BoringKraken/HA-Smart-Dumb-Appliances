"""Data coordinator for Smart Dumb Appliance."""
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_MESSAGE,
    CONF_SERVICE_REMINDER_COUNT,
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

    @property
    def formatted_last_update(self) -> str | None:
        """Return formatted last_update."""
        return self.last_update.isoformat() if self.last_update else None

    @property
    def formatted_start_time(self) -> str | None:
        """Return formatted start_time."""
        return self.start_time.isoformat() if self.start_time else None

    @property
    def formatted_end_time(self) -> str | None:
        """Return formatted end_time."""
        return self.end_time.isoformat() if self.end_time else None

    @property
    def formatted_cycle_duration(self) -> str:
        """Return formatted cycle_duration."""
        return str(self.cycle_duration) if self.cycle_duration else "0:00:00"

    @property
    def formatted_last_cycle_duration(self) -> str:
        """Return formatted last_cycle_duration."""
        return str(self.last_cycle_duration) if self.last_cycle_duration else "0:00:00"

    @property
    def formatted_total_duration(self) -> str:
        """Return formatted total_duration."""
        return str(self.total_duration) if self.total_duration else "0:00:00"

class SmartDumbApplianceCoordinator(DataUpdateCoordinator):
    """Coordinator for Smart Dumb Appliance data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{config_entry.data.get('name', 'Smart Dumb Appliance')}_coordinator",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=1),  # Regular update interval
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
        self._last_cycle_duration = None
        self._total_duration = timedelta(0)
        self.data = None
        self._initialized = False

        # Store the unsubscribe callback
        self._unsubscribe = None
        # Store listeners
        self._listeners = []

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
                # Return current data if available to maintain state persistence
                if self.data:
                    return self.data
                # Create empty data if no previous state exists
                return ApplianceData(
                    last_update=dt_util.utcnow(),
                    power_state=0.0,
                    power_kw=0.0,
                    is_running=False,
                    start_time=None,
                    end_time=None,
                    use_count=self._use_count if hasattr(self, '_use_count') else 0,
                    cycle_energy=0.0,
                    previous_cycle_energy=self._previous_cycle_energy if hasattr(self, '_previous_cycle_energy') else 0.0,
                    total_energy=self._total_energy if hasattr(self, '_total_energy') else 0.0,
                    cycle_cost=0.0,
                    previous_cycle_cost=self._previous_cycle_cost if hasattr(self, '_previous_cycle_cost') else 0.0,
                    total_cost=self._total_cost if hasattr(self, '_total_cost') else 0.0,
                    last_power=0.0,
                    last_power_time=None,
                    cycle_duration=None,
                    last_cycle_duration=self._last_cycle_duration if hasattr(self, '_last_cycle_duration') else None,
                    total_duration=self._total_duration if hasattr(self, '_total_duration') else timedelta(0),
                    service_status="disabled",
                    service_reminder_enabled=self.config_entry.data.get(CONF_SERVICE_REMINDER, False),
                    service_reminder_message=self.config_entry.data.get(CONF_SERVICE_REMINDER_MESSAGE, ""),
                    service_reminder_count=self.config_entry.data.get(CONF_SERVICE_REMINDER_COUNT, 0),
                    remaining_cycles=max(0, self.config_entry.data.get(CONF_SERVICE_REMINDER_COUNT, 0) - (self._use_count if hasattr(self, '_use_count') else 0))
                )

            try:
                current_power = float(power_state.state)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid power reading from sensor %s: %s", self._power_sensor, power_state.state)
                if self.data:
                    return self.data
                raise UpdateFailed("Invalid power reading")

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
                    self._last_cycle_duration = current_duration
                    self._total_duration += current_duration
                    self._last_cycle_end_time = self._end_time
                    _LOGGER.debug(
                        "Cycle ended - Previous cycle energy: %.3f kWh, cost: $%.2f, Duration: %s",
                        self._previous_cycle_energy,
                        self._previous_cycle_cost,
                        self._last_cycle_duration
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
                last_cycle_duration=self._last_cycle_duration,
                total_duration=self._total_duration,
                service_status="ok" if is_on else "disabled",
                service_reminder_enabled=self.config_entry.data.get(CONF_SERVICE_REMINDER, False),
                service_reminder_message=self.config_entry.data.get(CONF_SERVICE_REMINDER_MESSAGE, ""),
                service_reminder_count=self.config_entry.data.get(CONF_SERVICE_REMINDER_COUNT, 0),
                remaining_cycles=max(0, self.config_entry.data.get(CONF_SERVICE_REMINDER_COUNT, 0) - self._use_count)
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
        if not self._initialized:
            # Add startup delay only for initial setup
            await asyncio.sleep(10)  # 10 second delay
            
            # Subscribe to power sensor changes
            self._unsubscribe = async_track_state_change_event(
                self.hass,
                self._power_sensor,
                self._async_power_sensor_changed
            )
            
            # Initial data fetch with retry
            retry_count = 0
            max_retries = 3
            retry_delay = 5  # seconds
            
            while retry_count < max_retries:
                try:
                    await self.async_request_refresh()
                    if self.data is not None:
                        _LOGGER.info("Successfully initialized coordinator for %s", self._power_sensor)
                        self._initialized = True
                        return
                except Exception as err:
                    _LOGGER.warning(
                        "Attempt %d/%d failed to initialize coordinator: %s",
                        retry_count + 1,
                        max_retries,
                        err
                    )
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(retry_delay)
            
            _LOGGER.error(
                "Failed to initialize coordinator for %s after %d attempts",
                self._power_sensor,
                max_retries
            )
        else:
            # If already initialized, just ensure we're subscribed to updates
            if not self._unsubscribe:
                self._unsubscribe = async_track_state_change_event(
                    self.hass,
                    self._power_sensor,
                    self._async_power_sensor_changed
                )

    async def async_shutdown(self) -> None:
        """Clean up resources."""
        _LOGGER.debug("Shutting down coordinator for %s", self._power_sensor)
        
        # Clear all listeners
        self._listeners.clear()
        
        # Unsubscribe from state changes
        if self._unsubscribe:
            try:
                self._unsubscribe()
            except ValueError:
                # Ignore errors if the listener was already removed
                _LOGGER.debug("Listener already removed for %s", self._power_sensor)
            self._unsubscribe = None
        
        # Clear all state
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
        self._last_cycle_duration = None
        self._total_duration = timedelta(0)
        self.data = None
        self._initialized = False
        
        # Stop the update interval
        await super().async_shutdown()

    @callback
    def _async_power_sensor_changed(self, event) -> None:
        """Handle power sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            _LOGGER.debug("Power sensor %s state is None, skipping update", self._power_sensor)
            return
        
        _LOGGER.debug(
            "Power sensor %s changed: new_state=%s",
            self._power_sensor,
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

    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        """Listen for data updates."""
        self._listeners.append(update_callback)
        return lambda: self._listeners.remove(update_callback)

    def async_remove_listener(self, update_callback: Callable[[], None]) -> None:
        """Remove listener from data updates."""
        if update_callback in self._listeners:
            self._listeners.remove(update_callback)

    def async_set_updated_data(self, data: ApplianceData) -> None:
        """Set updated data and notify listeners."""
        self.data = data
        for listener in self._listeners:
            listener()

    async def async_shutdown(self) -> None:
        """Clean up resources."""
        _LOGGER.debug("Shutting down coordinator for %s", self._power_sensor)
        
        # Clear all listeners
        self._listeners.clear()
        
        # Unsubscribe from state changes
        if self._unsubscribe:
            try:
                self._unsubscribe()
            except ValueError:
                # Ignore errors if the listener was already removed
                _LOGGER.debug("Listener already removed for %s", self._power_sensor)
            self._unsubscribe = None
        
        # Clear all state
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
        self._last_cycle_duration = None
        self._total_duration = timedelta(0)
        self.data = None
        self._initialized = False
        
        # Stop the update interval
        await super().async_shutdown() 