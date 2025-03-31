## Work In Progress

#Smart Dumb Appliance

Smart Dumb Appliance is a custom integration for Home Assistant designed to monitor the energy usage of various appliances like washing machines, dishwashers, and even coffee makers. This integration allows you to track when these appliances start and finish, calculate electricity costs using a dynamic cost per kilowatt-hour, and provide service reminders.

## Features

- **Monitor Appliance Start/End**: Automatically detect when appliances turn on and off based on energy usage.
- **Dynamic Cost Calculation**: Use a Home Assistant Number helper to adjust and reflect current energy costs.
- **Configure Dead Zones and Debounce**: Set thresholds to avoid false triggers.
- **Service Reminders**: Notify after a set number of uses for maintenance tasks.
- **UI Configuration**: Configure easily within Home Assistant's UI.

## Installation

### Prerequisites
- HACS (Home Assistant Community Store) installed for easy management.

### Installation Steps

1. **Via HACS**:
    - Open the HACS tab in Home Assistant.
    - Click the "Three Dots" in the top Right Hand corner.
    - Click "Custom repositories"
    - Choose Type : Integration
    - Copy in the link to this repository: https://github.com/BoringKraken/HA-Smart-Dumb-Appliances

2. **Manual Installation**:
    - Download or clone this repository.
    - Copy the `smart_dumb_appliance` directory into the `custom_components` directory in your Home Assistant configuration directory.
    - Restart Home Assistant.

## Configuration

### Create a Number Helper

1. Navigate to "Configuration" > "Helpers" in Home Assistant.
2. Click "Add Helper" and choose "Number".
3. Configure the name, icon, minimum, maximum, and step. Note the entity ID (e.g., `input_number.energy_cost_per_kwh`).

### Configure the Integration Using the UI

1. Navigate to "Configuration" > "Devices & Services".
2. Click "Add Integration" and search for "Smart Dumb Appliance".
3. Follow prompts:
   - Enter appliance name.
   - Provide sensor entity ID (e.g., `sensor.washing_machine_energy`).
   - Provide entity ID for cost helper.
   - Configure additional parameters like dead zones, debounce time.

### Configuration Options

- **Name**: Display name for the appliance.
- **Sensor Entity ID**: Sensor providing energy data.
- **Dead Zone**: Energy threshold below which the appliance is off.
- **Debounce Time**: Time to confirm state changes.
- **Cost Helper Entity ID**: Used for calculating usage cost.
- **Service Reminder**: Use count for maintenance reminders.

## Usage

- Monitor appliance status via the Home Assistant dashboard.
- Receive maintenance reminders through Home Assistant notifications.

## Troubleshooting

- Verify energy sensors provide accurate values.
- Check Home Assistant logs (`Configuration` > `Logs`) for error messages related to this integration.

## Support

For any issues or feature requests, please visit the [GitHub repository](https://github.com/boringkraken/HA-Smart-Dumb-Appliances) to raise an issue or contribute.

By using this integration, you agree to this setup and understand the obligations under the chosen license.
