## Work In Progress

# Smart Dumb Appliance

A Home Assistant custom integration that turns your "dumb" appliances into smart ones by monitoring their power usage. This integration helps you track energy consumption, operating costs, and maintenance schedules for appliances that don't have built-in smart features.

## Features

- Monitors appliance power usage in real-time
- Automatically detects when appliances are running
- Tracks energy consumption and operating costs
- Provides service reminders based on usage
- Supports multiple appliances with different configurations
- Easy to configure through the Home Assistant UI

## Installation

### Method 1: HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Open Home Assistant and go to HACS
3. Click "Add Custom Repository"
4. Enter the following details:
   - Repository: `BoringKraken/HA-Smart-Dumb-Appliances`
   - Category: Integration
   - Name: Smart Dumb Appliance
5. Click "Add"
6. Find "Smart Dumb Appliance" in the HACS store
7. Click "Download"
8. Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from the [releases page](https://github.com/BoringKraken/HA-Smart-Dumb-Appliances/releases)
2. Extract the downloaded zip file
3. Copy the `custom_components/SmartDumbAppliance` folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

### Method 3: Git Clone

1. SSH into your Home Assistant instance
2. Navigate to the custom_components directory:
   ```bash
   cd /config/custom_components
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/BoringKraken/HA-Smart-Dumb-Appliances.git SmartDumbAppliance
   ```
4. Restart Home Assistant

## Configuration

After installation, you can add the integration through the Home Assistant UI:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Smart Dumb Appliance"
4. Click "Configure"
5. Enter the required information:
   - Device Name: A friendly name for your appliance
   - Power Sensor: Select the power monitoring sensor
   - Cost Sensor (Optional): Select a sensor that provides electricity cost per kWh
6. Click "Submit"

### Advanced Configuration

Click "Show Advanced Options" to configure additional settings:

- Start Watts: Power threshold that indicates the appliance has started
- Stop Watts: Power threshold that indicates the appliance has stopped
- Dead Zone: Minimum power threshold to consider appliance as "on"
- Debounce: Time to wait before confirming state changes
- Service Reminder: Enable usage tracking and maintenance reminders
- Service Reminder Count: Number of uses before showing a reminder
- Service Reminder Message: Custom message for the reminder

## Usage

Once configured, the integration will create several entities for each appliance:

- Energy Usage: Tracks total energy consumption
- Power State: Shows if the appliance is currently running
- Service Status: Indicates if maintenance is needed

You can use these entities in automations, dashboards, and scripts to:
- Monitor appliance usage
- Track energy costs
- Get maintenance reminders
- Create notifications for state changes

## Examples

### Basic Automation

```yaml
automation:
  - alias: "Notify when dishwasher is done"
    trigger:
      - platform: state
        entity_id: binary_sensor.dishwasher_power_state
        to: "off"
    action:
      - service: notify.notify
        data:
          message: "Dishwasher cycle complete"
```

### Energy Usage Tracking

```yaml
sensor:
  - platform: template
    sensors:
      dishwasher_daily_energy:
        value_template: >
          {% set energy = states('sensor.dishwasher_energy_usage') | float %}
          {{ energy | round(2) }}
        unit_of_measurement: kWh
```

## Troubleshooting

If you're having issues with the integration:

1. Check the Home Assistant logs for error messages
2. Verify your power sensor is working correctly
3. Ensure the watt thresholds are appropriate for your appliance
4. Try adjusting the debounce time if you get false readings
5. Make sure you have the latest version installed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
