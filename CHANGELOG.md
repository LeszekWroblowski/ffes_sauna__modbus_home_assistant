# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.11] - 2026-03-20

### Fixed
- Restored safety-first power semantics so Home Assistant only reports heating as `on` during actual `STATUS_HEAT`
- Prevented standby or ventilation states from appearing as active heating after Home Assistant restarts

## [1.0.10] - 2026-03-20

### Fixed
- Fixed sauna light entity registration for newer Home Assistant versions by declaring the required `ColorMode.ONOFF`

## [1.0.9] - 2026-03-20

### Added
- Added real Home Assistant services for `start_session`, `stop_session`, and `set_profile`
- Added controller-model-aware profile filtering based on `REG[50]`
- Added sauna light entity mapped to the FFES light output
- Added physical fan output switch mapped to the FFES 230V fan output
- Added Modbus connection validation during config flow setup

### Fixed
- Fixed binary sensor mappings for WiFi, server connection, and frost protection status
- Fixed climate state reporting so standby and ventilation are no longer shown as fully off
- Fixed profile handling so unsupported profiles are hidden and rejected when selected
- Fixed duplicated refresh requests after write operations

### Changed
- Updated integration behavior to align with FFES Modbus documentation for controller capabilities and output handling
- Improved runtime safeguards when changing profiles while the sauna is active

## [1.0.6] - 2025-10-30

### Fixed
- **CRITICAL**: Fixed register offset from 2 to 1 - data was shifted by one register causing incorrect readings
- **CRITICAL**: Fixed register count from 60 to 50 - prevented "ILLEGAL DATA ADDRESS" error
- Fixed climate entity HVAC mode not displaying correctly (added `is_on` and `is_heating` to coordinator data)
- Fixed AttributeError when using switches/controls - changed all `write_register()` calls to `async_write_register()`
- Fixed AttributeError when using coil switches - changed all `write_coil()` calls to `async_write_coil()`
- Fixed deprecated `self.config_entry` assignment in OptionsFlow (removed for Home Assistant 2025.12+ compatibility)
- Fixed excessive logging - changed verbose debug logs from INFO to DEBUG level
- Fixed coil count from 56 to 56 (verified from documentation)

### Added
- Added comprehensive CLAUDE.md documentation for AI-assisted development
- Added pymodbus version detection (v3.10+ uses `device_id` parameter, older uses `slave`)
- Added detailed debug logging for register values (REG[1]-REG[5] and REG[20])
- Added FFES_Modbus_0.1.pdf official documentation to repository

### Changed
- Updated all platform files to use async write methods (switch.py, number.py, select.py, climate.py)
- Improved coordinator error messages with register address information
- Updated documentation to reflect correct register addressing (REG[1] = physical address 1)

### Technical Details
- Register addressing now correct: FFES REG[1] = Modbus physical address 1 (not 0, not 2)
- Reading 50 registers from physical address 1 (addresses 1-50 for REG[1] to REG[50])
- Reading 56 coils from physical address 1 (addresses 1-56 for REG[1] to REG[56])
- Controller status properly mapped: STATUS_OFF=0, STATUS_HEAT=1, STATUS_VENT=2, STATUS_STBY=3

## [1.0.1] - 2025-10-29

### Fixed
- Fixed "500 Internal Server Error" when loading config flow
- Fixed pymodbus version conflict - changed from `==3.6.8` to `>=3.6.0` for compatibility with Home Assistant 2025.x
- Simplified config flow to avoid timeout issues
- Removed unnecessary validation during initial setup

### Changed
- Config flow no longer validates Modbus connection during setup (validation happens on first data refresh)
- Updated pymodbus requirement to `>=3.6.0` for better compatibility

## [1.0.0] - 2025-10-29

### Added
- Initial release of FFES Sauna Home Assistant integration
- Climate entity for temperature control
- Support for all 7 sauna profiles (Infrared, Dry, Wet, Ventilation, Steam Bath, CPIR, MIX)
- Sensor entities for temperature, humidity, status, and error monitoring
- Switch entities for power, ventilation, frost protection, and infrared mix
- Number entities for session time, ventilation time, aromatherapy, humidity, and CPIR groups
- Select entity for profile selection
- Binary sensors for error, heating, frost protection, WiFi and server connection status
- Services: start_session, stop_session, set_profile
- Config flow for easy GUI configuration
- Support for Modbus TCP protocol
- Polish and English translations
- Comprehensive documentation and examples

### Features
- Real-time monitoring of sauna temperature and status
- Remote control of all sauna functions
- Session timer management (1-2000 minutes)
- Humidity control for wet sauna and steam bath
- Aromatherapy intensity control
- CPIR infrared group power control
- Error code detection and display
- Frost protection mode
- Ventilation control
- Multiple sauna profile support

### Technical
- Built on pymodbus 3.6.8
- Async/await architecture
- Polling-based updates with configurable scan interval (5-120 seconds)
- Proper error handling and logging
- HACS compatible structure
- Follows Home Assistant integration best practices

## [Unreleased]

### Planned Features
- Auto-discovery support
- Session history tracking
- Energy consumption monitoring (if supported by hardware)
- Advanced automation templates
- Dashboard card templates
- Additional language translations

---

**Note:** This integration is not officially affiliated with FFES. It is a community-developed project based on the Modbus TCP protocol specification.
