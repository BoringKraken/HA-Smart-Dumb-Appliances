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
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfEnergy, UnitOfPower

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
    DOMAIN,
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
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create all sensors
    sensors = [
        SmartDumbApplianceBinarySensor(coordinator, config_entry),
        SmartDumbApplianceServiceSensor(coordinator, config_entry),
        SmartDumbAppliancePowerSensor(coordinator, config_entry),
        SmartDumbApplianceDurationSensor(coordinator, config_entry),
        SmartDumbApplianceEnergySensor(coordinator, config_entry),
        SmartDumbApplianceCostSensor(coordinator, config_entry),
    ]
    
    async_add_entities(sensors)

class SmartDumbApplianceBinarySensor(BinarySensorEntity):
    """Binary sensor representing the cycle state of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle State"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_state"
        self._attr_device_class = "power"
        self._attr_icon = "mdi:power"
        self._attr_extra_state_attributes = {
            "current_power": 0.0,
            "start_time": None,
            "end_time": None,
            "cycle_duration": None,
            "cycle_energy": 0.0,
            "cycle_cost": 0.0,
            "last_update": None,
        }

    @property
    def is_on(self) -> bool:
        """Return True if the appliance is running."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.is_running

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_power": data.power_state,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "cycle_duration": data.cycle_duration,
            "cycle_energy": data.cycle_energy,
            "cycle_cost": data.cycle_cost,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbApplianceServiceSensor(SensorEntity):
    """Sensor representing the service status of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the service status sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Service Status"
        self._attr_unique_id = f"{config_entry.entry_id}_service_status"
        self._attr_icon = "mdi:wrench"
        self._attr_extra_state_attributes = {
            "cycle_count": 0,
            "service_reminder_enabled": False,
            "service_reminder_message": "",
            "total_cycles_till_service": 0,
            "remaining_cycles": 0,
            "current_running_state": False,
            "last_update": None,
        }

    @property
    def native_value(self) -> str:
        """Return the service status."""
        if self.coordinator.data is None:
            return "ok"
        return self.coordinator.data.service_status

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "cycle_count": data.use_count,
            "service_reminder_enabled": data.service_reminder_enabled,
            "service_reminder_message": data.service_reminder_message,
            "total_cycles_till_service": data.service_reminder_count,
            "remaining_cycles": data.remaining_cycles,
            "current_running_state": data.is_running,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbAppliancePowerSensor(SensorEntity):
    """Sensor representing the current power usage of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the current power sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Current Power"
        self._attr_unique_id = f"{config_entry.entry_id}_current_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_extra_state_attributes = {
            "start_threshold": config_entry.data.get(CONF_START_WATTS, DEFAULT_START_WATTS),
            "stop_threshold": config_entry.data.get(CONF_STOP_WATTS, DEFAULT_STOP_WATTS),
            "running_state": False,
            "power_sensor": config_entry.data[CONF_POWER_SENSOR],
            "last_update": None,
        }

    @property
    def native_value(self) -> float:
        """Return the current power usage."""
        if self.coordinator.data is None:
            return 0.0
        return self.coordinator.data.power_state

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "running_state": data.is_running,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbApplianceDurationSensor(SensorEntity):
    """Sensor for tracking appliance cycle duration."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the duration sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_name = f"{config_entry.data.get(CONF_DEVICE_NAME, 'Smart Dumb Appliance')} Cycle Duration"
        self._attr_unique_id = f"{config_entry.entry_id}_duration"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:timer"

    @property
    def native_value(self) -> timedelta | None:
        """Return the current Cycle duration."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.cycle_duration

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {
                "current_cycle_duration": None,
                "previous_cycle_duration": "0:00:00",
                "total_duration": "0:00:00",
                "last_update": None,
            }
            
        # Convert timedelta objects to strings
        current_duration = str(self.coordinator.data.cycle_duration) if self.coordinator.data.cycle_duration else None
        previous_duration = str(self.coordinator.data.last_cycle_duration) if self.coordinator.data.last_cycle_duration else "0:00:00"
        total_duration = str(self.coordinator.data.total_duration) if self.coordinator.data.total_duration else "0:00:00"
        
        return {
            "current_cycle_duration": current_duration,
            "previous_cycle_duration": previous_duration,
            "total_duration": total_duration,
            "last_update": self.coordinator.data.last_update.isoformat() if self.coordinator.data.last_update else None,
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbApplianceEnergySensor(SensorEntity):
    """Sensor representing the cycle energy usage of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cycle energy sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle Energy"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_energy"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_extra_state_attributes = {
            "current_cycle_energy": 0.0,
            "previous_cycle_energy": 0.0,
            "total_energy": 0.0,
            "last_update": None,
        }

    @property
    def native_value(self) -> float:
        """Return the current cycle energy usage."""
        if self.coordinator.data is None:
            return 0.0
        return self.coordinator.data.cycle_energy

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_cycle_energy": data.cycle_energy,
            "previous_cycle_energy": data.previous_cycle_energy,
            "total_energy": data.total_energy,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbApplianceCostSensor(SensorEntity):
    """Sensor representing the cycle cost of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cycle cost sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_name = f"{config_entry.data.get('name', 'Smart Dumb Appliance')} Cycle Cost"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "USD"
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:currency-usd"
        self._attr_extra_state_attributes = {
            "current_cycle_cost": 0.0,
            "previous_cycle_cost": 0.0,
            "total_cost": 0.0,
            "last_update": None,
        }

    @property
    def native_value(self) -> float:
        """Return the current cycle cost."""
        if self.coordinator.data is None:
            return 0.0
        return self.coordinator.data.cycle_cost

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        if self.coordinator.data is None:
            return self._attr_extra_state_attributes

        data = self.coordinator.data
        self._attr_extra_state_attributes.update({
            "current_cycle_cost": data.cycle_cost,
            "previous_cycle_cost": data.previous_cycle_cost,
            "total_cost": data.total_cost,
            "last_update": data.last_update,
        })
        return self._attr_extra_state_attributes

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

class SmartDumbApplianceCycleStateSensor(SensorEntity):
    """Sensor representing the cycle state of a smart dumb appliance."""

    def __init__(
        self,
        coordinator: SmartDumbApplianceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the cycle state sensor."""
        super().__init__()
        self.coordinator = coordinator
        self._attr_name = f"{config_entry.data.get(CONF_DEVICE_NAME, 'Smart Dumb Appliance')} Cycle State"
        self._attr_unique_id = f"{config_entry.entry_id}_cycle_state"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:power"

    @property
    def native_value(self) -> float | None:
        """Return the current power reading."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.power_state

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {
                "current_power": None,
                "start_time": None,
                "end_time": None,
                "cycle_duration": "0:00:00",
                "cycle_energy": 0.0,
                "cycle_cost": 0.0,
                "last_update": None,
            }
            
        # Convert timedelta to string
        cycle_duration = str(self.coordinator.data.cycle_duration) if self.coordinator.data.cycle_duration else "0:00:00"
        
        return {
            "current_power": self.coordinator.data.power_state,
            "start_time": self.coordinator.data.start_time.isoformat() if self.coordinator.data.start_time else None,
            "end_time": self.coordinator.data.end_time.isoformat() if self.coordinator.data.end_time else None,
            "cycle_duration": cycle_duration,
            "cycle_energy": self.coordinator.data.cycle_energy,
            "cycle_cost": self.coordinator.data.cycle_cost,
            "last_update": self.coordinator.data.last_update.isoformat() if self.coordinator.data.last_update else None,
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state) 