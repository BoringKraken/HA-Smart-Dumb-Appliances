# Smart Dumb Appliance

A Home Assistant integration that monitors "dumb" appliances by tracking their power usage patterns. This integration helps you understand when appliances are running, their energy consumption, and when they need maintenance.

## Features

- **Energy Monitoring**: Tracks total energy usage in kWh
- **Power State Detection**: Automatically detects when appliances are running
- **Cost Tracking**: Calculates operating costs based on energy rates
- **Service Reminders**: Tracks usage and reminds you when maintenance is needed
- **Smart Icons**: Automatically selects appropriate icons based on appliance type
- **Status Colors**: Visual indicators for different states (on/off/service needed)
- **Detailed Logging**: Comprehensive logging for troubleshooting

## Sensors

The integration creates three sensors for each appliance:

1. **Energy Usage Sensor** (`sensor.{appliance_name}_energy_usage`)
   - Shows total energy consumption in kWh
   - Displays current power usage in watts
   - Tracks operating costs
   - Shows usage history and statistics
   - Precision: 2 decimal places

2. **Power State Sensor** (`binary_sensor.{appliance_name}_power_state`)
   - Indicates if the appliance is currently running
   - Updates based on power consumption thresholds
   - Includes colored status indicators

3. **Service Status Sensor** (`sensor.{appliance_name}_service_status`)
   - Shows maintenance status
   - Tracks usage count
   - Provides service reminders
   - States: "ok", "needs_service", "disabled"

## Configuration

### Basic Setup

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Smart Dumb Appliance"
4. Enter the following information:
   - **Device Name**: Name of your appliance
   - **Power Sensor**: Entity ID of your power monitoring sensor
   - **Cost Sensor** (optional): Entity ID of your energy cost sensor

### Advanced Settings

- **Start Watts**: Power threshold to detect appliance start (default: 5.0W)
- **Stop Watts**: Power threshold to detect appliance stop (default: 2.0W)
- **Dead Zone**: Minimum power threshold (default: 1.0W)
- **Debounce Time**: Minimum time between state changes (default: 5 seconds)
- **Service Reminder**: Enable/disable maintenance tracking
- **Service Count**: Number of uses before maintenance reminder
- **Service Message**: Custom message for maintenance reminders

## Examples

### Basic Configuration
```yaml
device_name: "Washing Machine"
power_sensor: "sensor.washing_machine_power"
cost_sensor: "sensor.electricity_cost"
```

### With Service Reminders
```yaml
device_name: "Dishwasher"
power_sensor: "sensor.dishwasher_power"
service_reminder: true
service_reminder_count: 30
service_reminder_message: "Time to clean the filter"
```

## Troubleshooting

### Common Issues

1. **Appliance not detected as running**
   - Check if power sensor is reporting correct values
   - Adjust start/stop watt thresholds
   - Verify dead zone setting

2. **Incorrect energy calculations**
   - Ensure power sensor updates frequently
   - Check power sensor unit (should be watts)
   - Verify cost sensor unit (should be cost per kWh)

3. **Service reminders not working**
   - Enable service reminders in configuration
   - Check service count threshold
   - Verify notification system is configured

### Logging

Enable debug logging for detailed information:
```yaml
logger:
  logs:
    custom_components.smart_dumb_appliance: debug
```

## Contributing

Feel free to submit issues and enhancement requests! 