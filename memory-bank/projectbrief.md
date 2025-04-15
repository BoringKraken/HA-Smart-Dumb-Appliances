# Smart Dumb Appliance Integration Project Brief

## Overview
The Smart Dumb Appliance integration is designed to monitor and track the energy usage and operational status of "dumb" appliances (appliances without built-in smart capabilities) by using power consumption data from a power monitoring sensor.

## Core Requirements

1. **Power State Detection**
   - Monitor power consumption to determine if an appliance is running based on configurable thresholds
   - Support start/stop wattage thresholds with debounce periods
   - Track real-time power usage

2. **Energy Tracking**
   - Calculate cumulative energy consumption (kWh)
   - Track cost based on energy rates
   - Record per-cycle energy and cost metrics
   - Log cycle start and end times

3. **Service Status Monitoring**
   - Count appliance usage cycles
   - Provide configurable service reminders
   - Display maintenance status indicators
   - Track service intervals

4. **Entity Management**
   - Create appropriate entities for each tracked metric
   - Support proper entity removal and cleanup
   - Handle device renaming gracefully
   - Maintain entity state across Home Assistant restarts

5. **Technical Requirements**
   - Integration must be responsive and efficient
   - Properly handle errors and missing sensors
   - Support clean uninstallation and config updates
   - Follow Home Assistant integration best practices

## Current Status and Priorities

### Recently Addressed Issues
1. Fixed entity removal issues during appliance deletion
2. Added startup delay to ensure proper dependency loading
3. Improved error handling in the coordinator
4. Fixed listener cleanup in sensors
5. Enhanced device/entity renaming support

### Current Priorities
1. Ensure proper entity cleanup and removal
2. Maintain seamless device name updates
3. Optimize update intervals for better performance
4. Improve robustness against power sensor failures

## Success Criteria
- No errors during installation, configuration, or removal
- Accurate power state detection with minimal false positives
- Proper tracking of energy usage and costs
- Clear service status indicators
- Smooth upgrade path for existing users 