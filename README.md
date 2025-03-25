# HA-Smart-Dumb-Appliances
HA: Smart Dumb Appliances

Smart Dumb Appliance is a custom integration for Home Assistant designed to monitor the energy usage of various appliances, such as washing machines, dishwashers, and even coffee makers. This integration allows you to track when these appliances start and finish, calculate their electricity costs, and provide service reminders.

## Features

- **Monitor Appliance Start/End**: Automatically detect when appliances start and stop based on energy usage.
- **Configure Dead Zones and Debounce**: Set thresholds to avoid false triggers.
- **Cost Calculation**: Calculate how much each appliance costs to run using configurable kWh pricing.
- **Service Reminders**: Get notified after a set number of uses for maintenance tasks.
- **UI Configuration**: Easily configure within Home Assistant's UI.

## Installation

### Prerequisites
- HACS (Home Assistant Community Store) installed for easy management.

### Installation Steps

1. **Via HACS:**
    - Open the HACS tab in your Home Assistant interface.
    - Go to "Integrations" and click the "+" button.
    - Search for 'Smart Dumb Appliance' and install it.

2. **Manual Installation:**
    - Download or clone this repository.
    - Copy the `smart_dumb_appliance` directory into the `custom_components` directory in your Home Assistant configuration directory.
    - Restart Home Assistant.

## Configuration

### Using Home Assistant UI

1. Navigate to "Configuration" > "Devices & Services".
2. Click "Add Integration" and search for "Smart Dumb Appliance".
3. Follow the prompts to set up each appliance you wish to monitor:
   - Enter a name for the appliance.
   - Provide the sensor entity ID (e.g., `sensor.washing_machine_energy`).
   - Configure optional parameters like dead zone, debounce time, and kWh pricing.

### Configuration Options

- **Name**: The display name for the appliance.
- **Sensor Entity ID**: The sensor providing energy data (must be preconfigured in Home Assistant).
- **Dead Zone**: Energy threshold below which the appliance is considered off.
- **Debounce Time**: Wait period to confirm state changes.
- **Cost Per kWh**: Rate used for calculating usage cost.
- **Service Reminder**: Use count before a maintenance reminder is issued.

## Usage

- Once set up, the integration will monitor the energy usage of your configured appliances.
- Check the status of each appliance through your Home Assistant dashboard.
- Receive service reminders in Home Assistant notifications.

## Troubleshooting

- Ensure the energy sensors are correctly set up and report accurate values.
- Verify the Home Assistant logs (`Configuration` > `Logs`) for any error messages related to this integration.

## Support

For any issues or feature requests, please visit the [GitHub repository](https://github.com/your-username/home-assistant-energy-monitor) to raise an issue or contribute.

## License

This project is licensed under the [MIT License](LICENSE).

---

By using this integration, you agree to this setup and understand the obligations under the chosen license.
