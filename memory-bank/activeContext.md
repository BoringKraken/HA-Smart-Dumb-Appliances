# Smart Dumb Appliance Integration: Active Context

## Current Work Focus

### Entity Cleanup and Management
The primary focus is enhancing the robustness of entity cleanup and management during integration unload and device rename operations. This includes:

1. Fixing issues with entity removal during appliance deletion
2. Ensuring proper listener cleanup during entity removal
3. Handling device and entity name updates correctly
4. Preventing orphaned entities in the entity registry

### Initialization Improvements
Secondary focus is on improving the initialization process to handle dependencies and startup conditions more gracefully:

1. Implementing startup delay to ensure dependencies are loaded
2. Adding retry mechanisms for initial data fetching
3. Improving error handling during coordinator setup
4. Preserving fast update intervals after initial setup

### Debounce Timer Changes
- Implementation of separate start and end debounce timers
- Migration from single debounce to dual debounce configuration
- Fine-tuning of default debounce values
- Updating binary sensor to use new debounce configuration

## Recent Changes

### Entity Removal Enhancements
- Added robust error handling in `async_unload_entry`
- Implemented two-phase entity removal to avoid dictionary iteration errors
- Fixed listener cleanup in sensor classes
- Added proper coordinator shutdown sequence

### Coordinator Improvements
- Added startup delay and retry logic
- Implemented `_initialized` flag to differentiate between first startup and subsequent updates
- Fixed update interval handling to maintain responsiveness
- Added comprehensive error handling and logging

### Sensor Cleanup
- Fixed `async_will_remove_from_hass` to use correct callback reference
- Added error handling for listener removal
- Added debug logging for troubleshooting
- Ensured proper callback management

### Device Rename Handling
- Added device registry update support
- Implemented entity name updates during rename operations
- Preserved entity_id consistency
- Added debug logging for rename operations

### Debounce Timer Changes
- Added separate start (5s) and end (15s) debounce timers
- Implemented migration logic for existing installations
- Updated configuration UI to support independent debounce settings
- Removed Final type hints from configurable constants
- Enhanced coordinator state tracking for debounce conditions
- Updated binary sensor to use new debounce configuration
- Added debounce values to binary sensor attributes

## Next Steps

### Short-term Tasks
1. **Validation Testing**: Test entity removal and rename operations across various scenarios
2. **Documentation Updates**: Update README and inline documentation to reflect recent changes
3. **Error Message Improvement**: Enhance error messages for better troubleshooting
4. **Logging Optimization**: Review and optimize logging levels and content

### Medium-term Tasks
1. **UI Enhancement**: Improve configuration UI for better user experience
2. **State Restoration**: Enhance state restoration after Home Assistant restarts
3. **Performance Optimization**: Review and optimize update intervals and calculations
4. **Threshold Improvement**: Make power thresholds more dynamic and self-adjusting

### Long-term Features
1. **Advanced Analytics**: Add more comprehensive energy usage analytics
2. **Anomaly Detection**: Implement abnormal power usage detection
3. **Dashboard Integration**: Create custom dashboard cards for better visualization
4. **Multi-power Sensor**: Support for multiple power sensors per appliance

## Active Decisions and Considerations

### Architectural Decisions
1. **Coordinator-Centric Logic**: All business logic and state calculations remain in the coordinator
2. **Entity Registry Management**: Explicit management of entity registry entries rather than relying on automatic cleanup
3. **Listener Handling**: Use of proper async listeners with robust error handling
4. **Update Strategy**: Fast updates (1 second) after initial setup with deferred startup

### Technical Trade-offs
1. **Initial Delay vs. Reliability**: Added startup delay improves reliability at the cost of slightly longer initial setup
2. **Explicit Cleanup vs. Simplicity**: More explicit cleanup code increases complexity but improves robustness
3. **Error Handling vs. Performance**: Comprehensive error handling adds overhead but improves stability
4. **Update Frequency vs. Resource Usage**: Faster updates improve responsiveness but increase resource usage

### User Experience Considerations
1. **Entity Naming**: Ensuring entity names update correctly when device is renamed
2. **Error Visibility**: Making errors visible and understandable to users
3. **Configuration Simplicity**: Keeping configuration options simple while providing necessary flexibility
4. **Performance Impact**: Balancing feature richness with performance impact

### Debounce Timer Decisions
1. **Separate Start/End Timers**: Using different debounce times for start (5s) and end (15s) conditions
2. **Migration Strategy**: Preserving existing debounce values during migration
3. **Configuration UI**: Providing clear controls for both debounce settings
4. **Default Values**: Using conservative defaults that can be adjusted by users 