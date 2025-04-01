"""
Sensor platform for Smart Dumb Appliance.

This module creates sensors that monitor an appliance's energy usage and status.
It includes:
- Main energy sensor (kWh) with detailed attributes
- Binary sensor for on/off state
- Service status sensor for maintenance tracking
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from difflib import SequenceMatcher
import base64
from io import BytesIO
from PIL import Image, ImageDraw

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfEnergy

from .const import (
    CONF_POWER_SENSOR,
    CONF_COST_SENSOR,
    CONF_START_WATTS,
    CONF_STOP_WATTS,
    CONF_DEBOUNCE,
    CONF_SERVICE_REMINDER,
    CONF_SERVICE_REMINDER_COUNT,
    CONF_SERVICE_REMINDER_MESSAGE,
    DEFAULT_START_WATTS,
    DEFAULT_STOP_WATTS,
    DEFAULT_DEBOUNCE,
    DEFAULT_SERVICE_REMINDER_COUNT,
    ATTR_POWER_USAGE,
    ATTR_TOTAL_COST,
    ATTR_LAST_UPDATE,
    ATTR_START_TIME,
    ATTR_END_TIME,
    ATTR_USE_COUNT,
    ATTR_LAST_SERVICE,
    ATTR_NEXT_SERVICE,
    ATTR_SERVICE_MESSAGE,
    CONF_DEVICE_NAME,
)
from .coordinator import SmartDumbApplianceCoordinator

# Set up logging for this module
_LOGGER = logging.getLogger(__name__)

# Status colors for different states
STATUS_COLORS = {
    # Service status colors
    "ok": "#4CAF50",  # Green
    "needs_service": "#FFC107",  # Amber
    "disabled": "#9E9E9E",  # Grey
    "warning": "#FF9800",  # Orange
    "error": "#F44336",  # Red
    
    # Power state colors
    "on": "#4CAF50",  # Green
    "off": "#9E9E9E",  # Grey
    "standby": "#FFC107",  # Amber
    
    # Maintenance colors
    "maintenance": "#2196F3",  # Blue
    "cleaning": "#00BCD4",  # Cyan
    "filter": "#3F51B5",  # Indigo
    
    # Energy usage colors
    "high_usage": "#F44336",  # Red
    "low_usage": "#4CAF50",  # Green
    "efficient": "#4CAF50",  # Green
    "inefficient": "#FF9800",  # Orange
}

# Icon mapping for common appliances
APPLIANCE_ICONS = {
    # Kitchen appliances
    "dishwasher": "mdi:dishwasher",
    "washing machine": "mdi:washing-machine",
    "dryer": "mdi:tumble-dryer",
    "refrigerator": "mdi:fridge",
    "freezer": "mdi:fridge-outline",
    "oven": "mdi:stove",
    "microwave": "mdi:microwave",
    "toaster": "mdi:toaster-oven",
    "kettle": "mdi:kettle",
    "coffee maker": "mdi:coffee-maker",
    "blender": "mdi:blender",
    "food processor": "mdi:food-processor",
    
    # HVAC
    "air conditioner": "mdi:air-conditioner",
    "heater": "mdi:radiator",
    "fan": "mdi:fan",
    "heat pump": "mdi:heat-pump",
    
    # Water heating
    "water heater": "mdi:water-heater",
    "hot water": "mdi:water-heater",
    
    # Entertainment
    "tv": "mdi:television",
    "television": "mdi:television",
    "stereo": "mdi:speaker",
    "speaker": "mdi:speaker",
    
    # Office
    "computer": "mdi:desktop-classic",
    "printer": "mdi:printer",
    "monitor": "mdi:monitor",
    
    # Cleaning
    "vacuum": "mdi:vacuum",
    "robot vacuum": "mdi:robot-vacuum",
    "robot": "mdi:robot-vacuum",
    
    # Default icons for common words
    "washer": "mdi:washing-machine",
    "fridge": "mdi:fridge",
    "stove": "mdi:stove",
    "ac": "mdi:air-conditioner",
    "pc": "mdi:desktop-classic",
    "laptop": "mdi:laptop",
}

# Status icons for different states
STATUS_ICONS = {
    # Service status icons
    "ok": "mdi:check-circle",
    "needs_service": "mdi:alert-circle",
    "disabled": "mdi:information",
    "warning": "mdi:alert",
    "error": "mdi:close-circle",
    
    # Power state icons
    "on": "mdi:power-plug",
    "off": "mdi:power-plug-off",
    "standby": "mdi:power-sleep",
    
    # Maintenance icons
    "maintenance": "mdi:wrench",
    "cleaning": "mdi:broom",
    "filter": "mdi:air-filter",
    
    # Energy usage icons
    "high_usage": "mdi:lightning-bolt",
    "low_usage": "mdi:lightning-bolt-outline",
    "efficient": "mdi:leaf",
    "inefficient": "mdi:leaf-off",
}

def string_similarity(a: str, b: str) -> float:
    """
    Calculate the similarity between two strings.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        float: Similarity score between 0 and 1
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_appliance_icon(name: str) -> str:
    """
    Get the appropriate icon for an appliance based on its name.
    Uses fuzzy matching to find the best match.
    
    Args:
        name: The name of the appliance
        
    Returns:
        str: The MDI icon name
    """
    # Convert name to lowercase for case-insensitive matching
    name_lower = name.lower()
    
    # First try exact substring matching
    for appliance, icon in APPLIANCE_ICONS.items():
        if appliance in name_lower:
            _LOGGER.debug("Exact match found: icon %s for appliance %s", icon, name)
            return icon
    
    # If no exact match, try fuzzy matching
    best_match = None
    best_ratio = 0.6  # Minimum similarity threshold
    
    for appliance, icon in APPLIANCE_ICONS.items():
        ratio = string_similarity(name_lower, appliance)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = icon
    
    if best_match:
        _LOGGER.debug("Fuzzy match found: icon %s for appliance %s (similarity: %.2f)", 
                     best_match, name, best_ratio)
        return best_match
    
    # Default to a generic power icon if no match found
    _LOGGER.debug("No match found for %s, using default", name)
    return "mdi:power-plug"

def create_colored_icon(icon_name: str, color: str) -> str:
    """
    Create a colored icon by combining the icon with a colored background.
    
    Args:
        icon_name: The MDI icon name
        color: The color to apply (hex code)
        
    Returns:
        str: Base64 encoded PNG image
    """
    try:
        # Create a new image with a transparent background
        size = (24, 24)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a colored circle
        circle_radius = 12
        circle_center = (12, 12)
        draw.ellipse(
            [
                circle_center[0] - circle_radius,
                circle_center[1] - circle_radius,
                circle_center[0] + circle_radius,
                circle_center[1] + circle_radius
            ],
            fill=color
        )
        
        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except Exception as e:
        _LOGGER.error("Error creating colored icon: %s", e)
        return None

def get_status_color(status: str) -> str:
    """
    Get the appropriate color for a given status.
    
    Args:
        status: The current status
        
    Returns:
        str: The color hex code
    """
    return STATUS_COLORS.get(status, "#9E9E9E")  # Default to grey

def get_status_icon(status: str, power_state: bool = None) -> tuple[str, str]:
    """
    Get the appropriate icon and color for a given status and power state.
    
    Args:
        status: The current status
        power_state: Optional power state (True for on, False for off)
        
    Returns:
        tuple: (icon_name, color_hex)
    """
    # If we have a power state, combine it with the status
    if power_state is not None:
        if power_state:
            return STATUS_ICONS.get("on", "mdi:power-plug"), STATUS_COLORS.get("on", "#4CAF50")
        return STATUS_ICONS.get("off", "mdi:power-plug-off"), STATUS_COLORS.get("off", "#9E9E9E")
    
    # Otherwise return the status-specific icon and color
    return STATUS_ICONS.get(status, "mdi:information"), STATUS_COLORS.get(status, "#9E9E9E")

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Dumb Appliance sensors from a config entry."""
    # Get the configuration data
    config = config_entry.data
    device_name = config[CONF_DEVICE_NAME]

    # Create the coordinator
    coordinator = SmartDumbApplianceCoordinator(hass, config_entry)

    # Create and add the sensors
    entities = [
        SmartDumbApplianceCumulativeEnergySensor(hass, config_entry, coordinator),
        SmartDumbApplianceCurrentPowerSensor(hass, config_entry, coordinator),
        SmartDumbApplianceServiceSensor(hass, config_entry, coordinator),
    ]
    
    async_add_entities(entities)

    # Start the coordinator
    await coordinator.async_config_entry_first_refresh()

class SmartDumbApplianceBase:
    """Base class for Smart Dumb Appliance sensors."""
    
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, coordinator: SmartDumbApplianceCoordinator) -> None:
        """Initialize the base sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self._attr_name = config_entry.data.get(CONF_DEVICE_NAME, "Smart Dumb Appliance")
        self._attr_unique_id = f"{config_entry.entry_id}"
        
        # Load configuration
        self._power_sensor = config_entry.data[CONF_POWER_SENSOR]
        self._cost_sensor = config_entry.data.get(CONF_COST_SENSOR)
        self._start_watts = config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS)
        self._stop_watts = config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS)
        self._debounce = config_entry.data.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)
        self._service_reminder = config_entry.data.get(CONF_SERVICE_REMINDER, False)
        self._service_reminder_count = config_entry.data.get(CONF_SERVICE_REMINDER_COUNT, DEFAULT_SERVICE_REMINDER_COUNT)
        self._service_reminder_message = config_entry.data.get(CONF_SERVICE_REMINDER_MESSAGE, "Time for maintenance")
        
        # Get appropriate icon based on appliance name
        self._attr_icon = get_appliance_icon(self._attr_name)
        
        # Initialize state tracking
        self._last_update = None
        self._last_power = 0.0
        self._total_energy = 0.0
        self._total_cost = 0.0
        self._start_time = None
        self._end_time = None
        self._use_count = 0
        self._last_service = None
        self._next_service = None
        self._was_on = False
        self._cycle_energy = 0.0
        self._cycle_cost = 0.0

        # Log initialization with sensor type
        sensor_type = self.__class__.__name__.replace('SmartDumbAppliance', '').replace('Sensor', '')
        _LOGGER.info(
            "Initializing %s (%s) with power sensor %s (start: %.1fW, stop: %.1fW)",
            self._attr_name,
            sensor_type,
            self._power_sensor,
            self._start_watts,
            self._stop_watts
        )

    @property
    def should_poll(self) -> bool:
        """Return False as we use the coordinator for updates."""
        return False

    async def async_update(self) -> None:
        """
        Update the sensor state.
        
        This method is called by the coordinator to update the sensor's state.
        It ensures that:
        1. The coordinator's data is up to date
        2. The power sensor state is read and processed
        3. All relevant attributes are updated
        4. State changes are logged for debugging
        """
        # Wait for the coordinator to update
        await self.coordinator.async_request_refresh()
        
        try:
            # Get the latest data from the coordinator
            data = self.coordinator.data
            if data is None:
                _LOGGER.warning("No data available from coordinator for %s", self._attr_name)
                return

            # Update the sensor state from coordinator data
            self._last_update = data.last_update
            self._last_power = data.power_state
            self._was_on = data.is_running
            self._start_time = data.start_time
            self._end_time = data.end_time
            self._use_count = data.use_count
            self._cycle_energy = data.cycle_energy
            self._cycle_cost = data.cycle_cost

            # Log the update
            _LOGGER.debug(
                "Updated %s: %.1fW (running: %s, last_update: %s)",
                self._attr_name,
                self._last_power,
                self._was_on,
                self._last_update
            )

        except Exception as err:
            _LOGGER.error(
                "Error updating %s: %s",
                self._attr_name,
                err
            )

    def _update_icon_and_color(self, status: str, power_state: bool = None) -> None:
        """
        Update the icon and color based on status.
        
        Args:
            status: The current status
            power_state: Optional power state
        """
        icon_name, color = get_status_icon(status, power_state)
        self._attr_icon = icon_name
        colored_icon = create_colored_icon(icon_name, color)
        if colored_icon:
            self._attr_entity_picture = colored_icon
        else:
            self._attr_entity_picture = None

class SmartDumbApplianceCumulativeEnergySensor(SmartDumbApplianceBase, SensorEntity):
    """
    Sensor for tracking cumulative energy usage of a smart dumb appliance.
    
    This sensor provides:
    - Total energy consumption in kWh
    - Total cost tracking
    - Last update timestamp
    - Start/End times of operation
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: SmartDumbApplianceCoordinator,
    ) -> None:
        """Initialize the cumulative energy sensor."""
        super().__init__(hass, config_entry, coordinator)
        self._attr_name = f"{self._attr_name} Cumulative Energy"
        self._attr_unique_id = f"{self._attr_name.lower().replace(' ', '_')}_cumulative_energy"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_available = True
        self._attr_extra_state_attributes = {
            "total_cost": 0.0,
            "last_update": None,
            "start_time": None,
            "end_time": None,
        }
        self._attr_has_entity_name = True
        self._attr_translation_key = "cumulative_energy"

    async def async_update(self) -> None:
        """Update the cumulative energy sensor state."""
        await super().async_update()
        self._attr_native_value = self._total_energy
        self._attr_extra_state_attributes.update({
            "total_cost": self._total_cost,
            "last_update": self._last_update,
            "start_time": self._start_time,
            "end_time": self._end_time,
        })

class SmartDumbApplianceCurrentPowerSensor(SmartDumbApplianceBase, SensorEntity):
    """
    Sensor for tracking current power usage and thresholds.
    
    This sensor provides real-time power consumption data and maintains
    various attributes for monitoring the appliance's operation:
    - Current power reading in watts
    - Power thresholds (start, stop)
    - Last update timestamp
    - Running state
    - Power sensor configuration
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: SmartDumbApplianceCoordinator,
    ) -> None:
        """
        Initialize the current power sensor.
        
        Args:
            hass: The Home Assistant instance
            config_entry: The configuration entry containing all settings
            coordinator: The update coordinator for managing updates
        """
        super().__init__(hass, config_entry, coordinator)
        self._attr_name = f"{self._attr_name} Current Power"
        self._attr_unique_id = f"{self._attr_name.lower().replace(' ', '_')}_current_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = "W"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_available = True
        self._attr_native_value = 0.0  # Initialize with 0
        
        # Define all possible attributes that this sensor can have
        self._attr_extra_state_attributes = {
            # Power thresholds and configuration
            "start_watts": self._start_watts,
            "stop_watts": self._stop_watts,
            "debounce": self._debounce,
            "power_sensor": self._power_sensor,
            "cost_sensor": self._cost_sensor,
            
            # Current state
            "is_running": False,
            "power_usage": 0.0,
            
            # Timing information
            "last_update": None,
        }
        self._attr_has_entity_name = True
        self._attr_translation_key = "current_power"
        _LOGGER.debug("Initialized current power sensor for %s", self._attr_name)

    async def async_update(self) -> None:
        """
        Update the current power sensor state.
        
        This method is called by the coordinator to update the sensor's state
        and attributes. It ensures that:
        1. The coordinator's data is up to date
        2. The sensor state and attributes are updated
        3. The icon and color are updated based on the power state
        4. Debug logging is performed for troubleshooting
        """
        try:
            # Wait for the coordinator to update
            await self.coordinator.async_request_refresh()
            
            # Get the latest data from the coordinator
            data = self.coordinator.data
            if data is None:
                _LOGGER.warning("No data available from coordinator for %s", self._attr_name)
                return

            # Update the main power value
            self._attr_native_value = data.power_state
            self._attr_available = True

            # Update all attributes with the latest values
            self._attr_extra_state_attributes.update({
                # Current state
                "is_running": data.is_running,
                "power_usage": data.power_state,
                
                # Timing information
                "last_update": data.last_update,
            })
            
            # Log the update for debugging
            _LOGGER.debug(
                "Updated current power sensor for %s: %.1fW (running: %s, last_update: %s)",
                self._attr_name,
                data.power_state,
                data.is_running,
                data.last_update
            )

            # Update the icon and color based on power state
            self._update_icon_and_color("on" if data.is_running else "off")

        except Exception as err:
            _LOGGER.error(
                "Error updating current power sensor %s: %s",
                self._attr_name,
                err
            )

class SmartDumbApplianceServiceSensor(SmartDumbApplianceBase, SensorEntity):
    """
    Sensor for tracking service status of an appliance.
    
    This sensor monitors the appliance's maintenance status and provides:
    - Current service status (ok, needs_service, disabled)
    - Usage count tracking
    - Service reminder scheduling
    - Last and next service dates
    - Service reminder configuration
    - Current running state
    - Current cycle energy and cost
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: SmartDumbApplianceCoordinator,
    ) -> None:
        """
        Initialize the service sensor.
        
        Args:
            hass: The Home Assistant instance
            config_entry: The configuration entry containing all settings
            coordinator: The update coordinator for managing updates
        """
        super().__init__(hass, config_entry, coordinator)
        self._attr_name = f"{self._attr_name} Service Status"
        self._attr_unique_id = f"{self._attr_name.lower().replace(' ', '_')}_service_status"
        self._attr_native_value = "OK"
        self._attr_icon = get_status_icon("ok")
        self._attr_has_entity_name = True
        self._attr_translation_key = "service_status"
        
        # Define all possible attributes that this sensor can have
        self._attr_extra_state_attributes = {
            # Timing information
            "last_update": None,
            
            # Usage tracking
            "use_count": 0,
            
            # Service information
            "last_service": None,
            "next_service": None,
            
            # Service reminder configuration
            "service_reminder_enabled": False,
            "service_reminder_count": 0,
            "service_reminder_message": None,
            
            # Current state
            "is_running": False,
            "cycle_energy": 0.0,
            "cycle_cost": 0.0,
        }

    async def async_update(self) -> None:
        """
        Update the service sensor state.
        
        This method is called by the coordinator to update the sensor's state
        and attributes. It:
        1. Gets the latest state from the base class
        2. Updates all service-related attributes
        3. Determines the current service status
        4. Updates the icon and color based on status
        5. Logs state changes for debugging
        """
        # First update the base class to get the latest state
        await super().async_update()
        
        # Update all attributes with the latest values
        self._attr_extra_state_attributes.update({
            # Timing information
            "last_update": self._last_update,
            
            # Usage tracking
            "use_count": self._use_count,
            
            # Service information
            "last_service": self._last_service,
            "next_service": self._next_service,
            
            # Service reminder configuration
            "service_reminder_enabled": self._service_reminder,
            "service_reminder_count": self._service_reminder_count,
            "service_reminder_message": self._service_reminder_message if self._service_reminder else None,
            
            # Current state
            "is_running": self._was_on,
            "cycle_energy": self._cycle_energy,
            "cycle_cost": self._cycle_cost,
        })
        
        # Determine the current service status
        if not self._service_reminder:
            self._attr_native_value = "disabled"
            self._update_icon_and_color("disabled")
        elif self._use_count >= self._service_reminder_count:
            self._attr_native_value = "needs_service"
            self._update_icon_and_color("needs_service")
        else:
            self._attr_native_value = "ok"
            self._update_icon_and_color("ok")
            
        # Log the update for debugging
        _LOGGER.debug(
            "Updated service sensor for %s: %s (current: %.1fW, use count: %d/%d, last_update: %s, running: %s, cycle energy: %.3f kWh, cycle cost: %.2f)",
            self._attr_name,
            self._attr_native_value,
            self._last_power,
            self._use_count,
            self._service_reminder_count,
            self._last_update,
            self._was_on,
            self._cycle_energy,
            self._cycle_cost
        ) 