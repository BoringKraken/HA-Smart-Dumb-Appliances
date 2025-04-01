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

### 1. Current Power Sensor
Attributes:
- Current power reading (W)
- Power thresholds (start/stop watts)
- Running state
- Power sensor configuration
- Last update timestamp

### 2. Binary Sensor (Power State)
Attributes:
- On/Off state
- Current power usage
- Start/End times
- Power sensor configuration
- Last update timestamp

### 3. Cumulative Energy Sensor
Attributes:
- Total energy consumption all time (kWh)
- Total energy consumption for the day (kWh)
- Total energy consumption for the month (kWh)
- Total energy consumption for the Cycle (kWh)
- Total cost all time ($0.00)
- Total cost for the day ($0.00)
- Total cost for the month ($0.00)
- Total cost for the Cycle  ($0.00)
- Cycle Start time
- Cycle End time
- Last update timestamp


### 4. Service Status Sensor
Attributes:
- Service status (ok/needs_service/disabled)
- Usage count
- Service reminder settings
- Last/Next service dates
- Current running state
- Current cycle energy and cost
- Last update timestamp

## Configuration Options

### Required Settings
- Device Name
- Power Sensor Entity ID

### Optional Settings
- Cost Sensor Entity ID
- Start Watts Threshold
- Stop Watts Threshold
- Dead Zone
- Debounce Period
- Service Reminder Settings
  - Enabled/Disabled
  - Usage Count Threshold
  - Reminder Message

## Default Values
- Start Watts: 10W
- Stop Watts: 5W
- Dead Zone: 2W
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

## Support
For issues or feature requests, please refer to the GitHub repository or Home Assistant community forums. 