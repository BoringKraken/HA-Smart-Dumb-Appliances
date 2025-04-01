# Smart Dumb Appliance Integration Primer

## Overview
The Smart Dumb Appliance integration is designed to monitor "dumb" appliances (those without smart capabilities) by tracking their energy consumption patterns. It provides real-time monitoring, usage statistics, and maintenance reminders through Home Assistant.

## Core Components

### 1. Coordinator (`coordinator.py`)
The coordinator is the central data manager for the integration. It:
- Fetches and processes power sensor data
- Tracks appliance state (running/not running)
- Manages timing information (start/end times)
- Calculates energy usage and costs
- Provides data to all sensors and binary sensors

### 2. Sensor Platform (`sensor.py`)
The sensor platform provides three types of sensors:
- **Cumulative Energy Sensor**: Tracks total energy consumption
- **Current Power Sensor**: Shows real-time power usage
- **Service Sensor**: Manages maintenance reminders

### 3. Binary Sensor Platform (`binary_sensor.py`)
The binary sensor platform provides:
- **Power State Sensor**: Indicates if the appliance is running
- Uses the coordinator's data to determine running state
- Provides power usage and timing information

### 4. Configuration Flow (`config_flow.py`)
Handles the integration setup process:
- Validates user input
- Creates configuration entries
- Manages options and settings

### 5. Constants (`const.py`)
Defines all integration constants:
- Configuration keys
- Default values
- Attribute names
- Platform names

### 6. Initialization (`__init__.py`)
Manages the integration lifecycle:
- Sets up the coordinator
- Initializes platforms
- Handles configuration entry loading/unloading
- Manages platform setup

## Data Flow
1. User configures the integration through the UI
2. `__init__.py` creates the coordinator
3. Coordinator fetches power sensor data
4. Sensors and binary sensors receive data from coordinator
5. UI updates with current values

## Key Features
- Real-time power monitoring
- Energy usage tracking
- Maintenance reminders
- State tracking (running/not running)
- Usage statistics
- Cost tracking (if cost sensor configured)

## Configuration Options
- Power sensor selection
- Start/Stop wattage thresholds
- Service reminder settings
- Cost sensor (optional)
- Debounce timing

## Best Practices
1. Always use the coordinator for data access
2. Keep state tracking in the coordinator
3. Use proper error handling
4. Log important events and errors
5. Follow Home Assistant's integration guidelines 