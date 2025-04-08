# Note for AI Assistants

This `PRIMER.md` document serves as the primary source of truth and "bible" for the Smart Dumb Appliance integration. It outlines the core design principles, technical architecture, development guidelines, and expected behavior.

**When assisting with code changes or generating new code for this repository, please strictly adhere to the information, patterns, and guidelines detailed within this document.** Ensure that all contributions are consistent with the described architecture, particularly the separation of concerns between the coordinator (handling calculations) and sensors (reading data). Refer back to this document frequently to maintain consistency and correctness.

# Smart Dumb Appliance Integration Primer

## Overview
The Smart Dumb Appliance integration is designed to monitor and track the energy usage and operational status of "dumb" appliances (appliances without built-in smart capabilities) by using power consumption data from a power monitoring sensor.

## Core Features

### 1. Power State Detection
- Monitors power consumption to determine if an appliance is running
- Configurable start and stop wattage thresholds
- Debounce period to prevent false triggers
- Real-time power usage tracking

### 2. Energy Tracking
- Cumulative energy consumption in kWh
- Cost tracking based on energy rates
- Per-cycle energy and cost monitoring
- Start and end time tracking for each cycle

### 3. Service Status Monitoring
- Usage count tracking
- Service reminder scheduling
- Maintenance status indicators
- Last and next service date tracking


## Entities

### 1. Binary Sensor (Cycle State)
Attributes:
- Cycle state (On/Off) - Primary Attribute/Sensor
- Current power reading (watts)
- Cycle Start time (Date/Time)
- Cycle End time (Date/Time)
- Total Duration for the current Cycle (hh:mm:ss updates in Real-Time)
- Total energy consumption for the current Cycle (0.000 kWh updates in Real-Time)
- Total cost for the current Cycle  ($0.000 updates in Real-Time)
- Last update timestamp

### 2. Service Status Sensor
Attributes:
- Service status (ok/needs_service/disabled) - Cycle state (On/Off) - Primary Attribute/Sensor
- Cycle count (e.g. 5)
- Service reminder enabled  (True/False)
- Service reminder message (text)
- Total Cycles till service (e.g. 20 (Previously Called - Service reminder count))
- Remainding Cycles till Service (e.g. 15)
- Current running state
- Last update timestamp

### 3. Current Power Sensor
Attributes:
- Current power reading (watts) - Cycle state (On/Off) - Primary Attribute/Sensor
- Start Cycle Threshold (watts)
- End Cycle Threshold (watts)
- Start Cycle Threshold (watts)
- Running state (True/False)
- Power sensor entity (Friendly Name)
- Last update timestamp (Date/Time)

### 4. Cycle Duration Sensor
Attributes:
- Total Duration for the current Cycle (hh:mm:ss updates in Real-Time) - Cycle state (On/Off) - Primary Attribute/Sensor
- Total Duration for the previous Cycle (hh:mm:ss)
- Total Duration for all Cycles (hh:mm:ss)
- Last update timestamps

### 5. Cycle Energy Sensor
Attributes:
- Total energy consumption for the current Cycle (0.000 kWh updates in Real-Time) - Cycle state (On/Off) - Primary Attribute/Sensor
- Total energy consumption for the previous Cycle (kWh)
- Total energy consumption for all Cycles (kWh)
- Last update timestamps

### 6. Cycle Cost Sensor
Attributes:
- Total cost for the current Cycle  ($0.000 updates in Real-Time) - Cycle state (On/Off) - Primary Attribute/Sensor
- Total cost for the previous Cycle  ($0.00)
- Total cost for all Cycles  ($0.00)
- Last update timestamps


## Current Configuration

### Configuration Options
- **Required Settings**
  - `device_name`: Name of the appliance
  - `power_sensor`: Entity ID of the power sensor
- **Optional Settings**
  - `cost_sensor`: Entity ID of the cost sensor
  - `start_watts`: Start wattage threshold
  - `stop_watts`: Stop wattage threshold
  - `debounce`: Debounce period
  - `service_reminder`: Service reminder settings
    - `enabled`: True/False
    - `count`: Usage count threshold
    - `message`: Reminder message

### Default Values
- Start Watts: 10W
- Stop Watts: 5W
- Debounce: 5 seconds
- Service Reminder Count: 30 uses

## Technical Requirements

### Dependencies
- Home Assistant Core
- Power monitoring sensor entity
- Optional cost sensor entity

### Update Frequency
- Coordinator updates every 1 second
- All entities receive updates through the coordinator

### Error Handling
- Graceful handling of missing sensors
- Error logging for invalid power readings
- State persistence across restarts

## Usage Examples

### Basic Configuration
```yaml
device_name: "Washing Machine"
power_sensor: "sensor.washing_machine_power"
```

### Advanced Configuration
```yaml
device_name: "Dishwasher"
power_sensor: "sensor.dishwasher_power"
cost_sensor: "sensor.electricity_cost"
start_watts: 5
stop_watts: 2
dead_zone: 0.5
debounce: 5
service_reminder:
  enabled: true
  count: 50
  message: "Time to clean the filter"
```

## Troubleshooting

### Common Issues
1. No power sensor found
   - Verify the power sensor entity ID
   - Check if the sensor is available in Home Assistant
   - Ensure the sensor is reporting valid power values

2. False power state detection
   - Adjust start/stop wattage thresholds
   - Increase debounce period
   - Check for power fluctuations

3. Missing updates
   - Verify coordinator is running
   - Check power sensor update frequency
   - Review Home Assistant logs for errors

### Debug Logging
- Detailed logging available for all state changes
- Power threshold crossing notifications
- Cycle summary information
- Service status updates

## Future Enhancements
2. More detailed energy analytics
5. Enhanced visualization options

## Development Guidelines

### Coordinator Responsibility
- **Centralized Calculations**: All state calculations, energy tracking, cost calculations, duration tracking, and service status logic MUST be handled within the `SmartDumbApplianceCoordinator`.
- **Sensor Role**: Sensors should ONLY read data directly from the coordinator's `data` attribute. Sensors should not perform any independent calculations or maintain their own state beyond what's provided by the coordinator.

### Commenting Code
- **Docstrings**: Use clear and concise docstrings for all classes and methods, explaining their purpose, arguments, and return values.
- **Complex Logic**: Add comments to explain complex algorithms, non-obvious logic, or potential edge cases.
- **User-Friendly**: Write comments that are easy for other developers (and future you) to understand. Avoid jargon where possible and explain the 'why' behind the code, not just the 'what'.
- **Keep Updated**: Ensure comments are kept up-to-date when code logic changes.

### Adding New Features
1. Extend `SmartDumbApplianceBase` for new sensor types if needed.
2. Update the coordinator's `ApplianceData` dataclass and calculation logic to include new data points.
3. Add appropriate logging for new features (see Debugging section).
4. Update documentation (`PRIMER.md`, docstrings) to reflect new features.

### Modifying Existing Features
1. **Coordinator First**: Make necessary changes to calculations or state logic within the `SmartDumbApplianceCoordinator`.
2. **Sensor Updates**: Update sensors only if they need to access new data points from the coordinator or change how they display existing data.
3. **Impact Review**: Review the impact on all sensors and the overall state management.
4. **Logging**: Maintain logging consistency across changes.
5. **Documentation**: Update documentation (`PRIMER.md`, docstrings) to reflect modifications.

### Debugging
1. Enable debug logging in Home Assistant's `configuration.yaml` for `custom_components.smart_dumb_appliance` to trace state changes and calculations.
2. Monitor coordinator updates and sensor processing in the logs.
3. Review state transitions and error conditions.

## Technical Architecture

### Data Flow
1. **Power Sensor → Coordinator**
   - The coordinator subscribes to power sensor changes.
   - Processes power readings to determine appliance state.
   - Calculates energy usage and timing information.
   - Maintains running state and use count.

2. **Coordinator → Sensors**
   - The coordinator provides data to all sensors.
   - Sensors receive updates through `async_update()`.
   - Each sensor type processes data differently:
     - **Current Power**: Direct power reading
     - **Cumulative Energy**: Energy calculations
     - **Service Status**: Use count and maintenance tracking

### Key Classes
1. **SmartDumbApplianceCoordinator**
   - Manages data updates and state tracking.
   - Handles power sensor subscriptions.
   - Calculates running state and energy usage.
   - Provides data to all sensors.

2. **SmartDumbApplianceBase**
   - Base class for all sensors.
   - Handles common initialization and updates.
   - Manages icon and color updates.
   - Provides shared attributes and methods.

3. **Sensor Types**
   - `SmartDumbApplianceBinarySensor`
   - `SmartDumbApplianceServiceSensor`
   - `SmartDumbApplianceCurrentPowerSensor`
   - `SmartDumbApplianceDurationSensor`
   - `SmartDumbApplianceEnergySensor`
   - `SmartDumbApplianceCostSensor`

### State Management
1. **Coordinator State**
   - `power_state`: Current power reading
   - `is_running`: Appliance running state
   - `start_time`: Cycle start timestamp
   - `end_time`: Cycle end timestamp
   - `use_count`: Total usage cycles
   - `cycle_energy`: Current cycle energy
   - `cycle_cost`: Current cycle cost

2. **Sensor State**
   - `native_value`: Primary sensor value
   - `extra_state_attributes`: Additional data
   - `icon`: Current display icon
   - `entity_picture`: Colored icon image

### Debug Logging
The integration provides extensive debug logging at key points:

1. **Coordinator Logging**
   - Power sensor state changes
   - Running state transitions
   - Energy calculations
   - Update timing information

2. **Sensor Logging**
   - Update receipt from coordinator
   - State changes
   - Energy calculations
   - Service status changes

3. **Binary Sensor Logging**
   - State transitions
   - Power readings
   - Timing information

### Common Issues and Solutions

1. No Updates from Coordinator
   - Check power sensor subscription
   - Verify coordinator initialization
   - Review coordinator logs
   - Check power sensor availability

2. Incorrect Running State
   - Verify start/stop thresholds
   - Check power sensor accuracy
   - Review debounce settings
   - Check coordinator logs

3. Missing Energy Calculations
   - Verify timing data
   - Check power readings
   - Review energy calculation logic
   - Check sensor logs

4. Service Status Issues
   - Verify use count tracking
   - Check service reminder settings
   - Review service status logic
   - Check service sensor logs

### Testing
1. Manual Testing
   - Power sensor changes
   - Running state transitions
   - Energy calculations
   - Service status updates

2. Logging Verification
   - Coordinator updates
   - Sensor processing
   - State changes
   - Error conditions 