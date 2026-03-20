# FFES Sauna Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/LeszekWroblowski/ffes_sauna__modbus_home_assistant.svg)](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/releases)

Home Assistant integration for FFES Sauna controllers with Modbus TCP support.

## Features

- 🌡️ **Temperature Control** - Set and monitor sauna temperature
- ⏱️ **Session Timer** - Control session duration (1-2000 minutes)
- 🎛️ **Controller-Aware Profiles** - Available profiles are filtered automatically based on the FFES controller model (`REG[50]`)
- 🎛️ **Multiple Profiles** - Support for all sauna types:
  - Infrared Sauna
  - Dry Sauna
  - Wet Sauna
  - Ventilation
  - Steam Bath
  - Infrared CPIR
  - Infrared MIX
- 💧 **Humidity Control** - Monitor and control humidity levels
- 🔄 **Ventilation Control** - Automatic ventilation management
- 💡 **Light Control** - Control the sauna light output from Home Assistant
- 🌀 **Physical Fan Output** - Control the FFES 230V fan output directly
- 🌿 **Aromatherapy** - Control aromatherapy intensity
- ⚠️ **Error Monitoring** - Real-time error code detection
- 🎚️ **Advanced Controls** - CPIR group controls, emergency settings, and more

## Supported Devices

This integration works with FFES sauna controllers that support Modbus TCP protocol (firmware 1.21/6.21 and newer).

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant`
6. Select category: "Integration"
7. Click "Add"
8. Find "FFES Sauna" in HACS and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/ffes_sauna` folder
3. Copy it to your `custom_components` directory in Home Assistant
4. Restart Home Assistant

## Configuration

### UI Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "FFES Sauna"
4. Enter your sauna controller details:
   - **Host**: IP address of your FFES controller (e.g., 192.168.0.208)
   - **Port**: Modbus TCP port (default: 502)
   - **Slave ID**: Modbus slave ID (default: 1)
   - **Name**: Friendly name for your sauna

### YAML Configuration (Alternative)

Add to your `configuration.yaml`:

```yaml
ffes_sauna:
  - host: 192.168.0.208
    port: 502
    slave: 1
    name: "My Sauna"
    scan_interval: 10
```

## Entities

After configuration, the integration creates the following entities:

### Climate
- `climate.sauna_thermostat` - Main temperature control

### Sensors
- `sensor.sauna_current_temperature` - Current temperature
- `sensor.sauna_target_temperature` - Target temperature
- `sensor.sauna_humidity` - Current humidity level
- `sensor.sauna_status` - Controller status (Off/Heating/Ventilation/Standby)
- `sensor.sauna_error_code` - Error code (0 = no error)
- `sensor.sauna_profile` - Current active profile
- `sensor.sauna_session_time_remaining` - Time remaining in session

### Switches
- `switch.sauna_power` - Turn sauna on/off
- `switch.sauna_ventilation` - Control ventilation
- `switch.sauna_frost_protection` - Enable/disable frost protection
- `switch.sauna_infrared_mix` - Enable/disable infrared mix mode
- `switch.sauna_fan_output` - Control the physical FFES fan output (230V)

### Lights
- `light.sauna_light` - Control the sauna light output

### Numbers
- `number.sauna_session_time` - Set session duration (1-2000 minutes)
- `number.sauna_ventilation_time` - Set ventilation time (1-2000 minutes)
- `number.sauna_aromatherapy` - Set aromatherapy intensity (0-100%)
- `number.sauna_vaporizer_humidity` - Set target humidity (0-100%)
- `number.sauna_cpir_group_1` - CPIR Group 1 power (1-100%)
- `number.sauna_cpir_group_2` - CPIR Group 2 power (1-100%)
- `number.sauna_cpir_group_3` - CPIR Group 3 power (1-100%)
- `number.sauna_cpir_group_4` - CPIR Group 4 power (1-100%)

### Select
- `select.sauna_profile` - Choose sauna profile from profiles supported by the connected controller

### Binary Sensors
- `binary_sensor.sauna_error` - Error status
- `binary_sensor.sauna_heating` - Heating status
- `binary_sensor.sauna_wifi_connection` - WiFi connection status
- `binary_sensor.sauna_server_connection` - Server connection status

## Services

### `ffes_sauna.start_session`
Start a sauna session with custom parameters.

If the requested profile is not supported by the connected controller model, the service call is rejected.

```yaml
service: ffes_sauna.start_session
target:
  entity_id: climate.sauna_thermostat
data:
  profile: 2  # 1=IR, 2=Dry, 3=Wet, 4=Vent, 5=Steam, 6=CPIR, 7=MIX
  temperature: 85
  duration: 60  # minutes
  humidity: 50  # optional, for wet sauna
```

### `ffes_sauna.stop_session`
Stop the current sauna session.

```yaml
service: ffes_sauna.stop_session
target:
  entity_id: climate.sauna_thermostat
```

### `ffes_sauna.set_profile`
Change sauna profile.

FFES allows profile changes only when the controller is `Off` or `Standby`.

```yaml
service: ffes_sauna.set_profile
target:
  entity_id: climate.sauna_thermostat
data:
  profile: "dry_sauna"  # or: infrared, wet_sauna, ventilation, steam_bath, infrared_cpir, infrared_mix
```

## Automation Examples

### Start Sauna Before Arriving Home

```yaml
automation:
  - alias: "Start Sauna When Leaving Work"
    trigger:
      - platform: zone
        entity_id: person.john
        zone: zone.work
        event: leave
    action:
      - service: ffes_sauna.start_session
        target:
          entity_id: climate.sauna_thermostat
        data:
          profile: 2  # Dry sauna
          temperature: 85
          duration: 90
```

### Notification When Sauna is Ready

```yaml
automation:
  - alias: "Notify When Sauna Ready"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sauna_current_temperature
        above: 80
    condition:
      - condition: state
        entity_id: switch.sauna_power
        state: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Sauna Ready!"
          message: "Your sauna has reached {{ states('sensor.sauna_current_temperature') }}°C"
```

### Auto-Start Sauna Daily

```yaml
automation:
  - alias: "Daily Evening Sauna"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: time
        weekday:
          - fri
          - sat
    action:
      - service: ffes_sauna.start_session
        target:
          entity_id: climate.sauna_thermostat
        data:
          profile: 2
          temperature: 85
          duration: 120
```

### Safety: Auto-Stop After Timeout

```yaml
automation:
  - alias: "Sauna Safety Timeout"
    trigger:
      - platform: state
        entity_id: switch.sauna_power
        to: "on"
        for:
          hours: 3
    action:
      - service: ffes_sauna.stop_session
        target:
          entity_id: climate.sauna_thermostat
      - service: notify.mobile_app
        data:
          title: "Sauna Auto-Stopped"
          message: "Sauna was automatically stopped after 3 hours for safety"
```

## Dashboard Card Example

```yaml
type: vertical-stack
cards:
  - type: thermostat
    entity: climate.sauna_thermostat
    name: Sauna Control
  
  - type: entities
    entities:
      - entity: sensor.sauna_current_temperature
        name: Current Temperature
      - entity: sensor.sauna_humidity
        name: Humidity
      - entity: sensor.sauna_status
        name: Status
      - entity: number.sauna_session_time
        name: Session Time
      - entity: select.sauna_profile
        name: Profile
      - entity: switch.sauna_ventilation
        name: Ventilation
      - entity: switch.sauna_fan_output
        name: Fan Output
      - entity: light.sauna_light
        name: Light
      - entity: number.sauna_aromatherapy
        name: Aromatherapy
  
  - type: conditional
    conditions:
      - entity: binary_sensor.sauna_error
        state: "on"
    card:
      type: alert
      entity: sensor.sauna_error_code
      name: Sauna Error
      state: "on"
```

## Error Codes

| Code | Description |
|------|-------------|
| 0 | No error |
| 1 | Temperature sensor disconnected or thermal fuse damaged |
| 2 | Temperature exceeded 125°C or 80°C for Wet/IR/Bath |
| 3 | Invalid temperature sensor reading |
| 4 | Rapid temperature increase |
| 5 | Low water level in heater tank |
| 6 | Humidity sensor reading error |
| 7 | Emergency switch active |
| 8 | Door open too long during session |
| 11 | CPIR module error L1 |
| 12 | CPIR module error L2 |
| 13 | CPIR module error L3 |

## Troubleshooting

### Integration Not Found
- Ensure you've restarted Home Assistant after installation
- Check that files are in `custom_components/ffes_sauna/`

### Connection Failed
- Verify the IP address is correct
- Ensure port 502 is open on your network
- Check that the FFES controller has Modbus TCP enabled
- Try pinging the controller from Home Assistant host

### Entities Not Updating
- Check the scan_interval setting (default: 10 seconds)
- Verify Modbus communication in Home Assistant logs
- Ensure no other device is blocking Modbus communication
- Check whether the selected profile is supported by your controller model

### Reading Errors
- Check that Slave ID matches your controller (usually 1)
- Verify your controller firmware version (1.21/6.21 or newer)

### Notes About Outputs
- `light.sauna_light` is mapped to the FFES light output (`OUT3_STATE`)
- `switch.sauna_fan_output` is mapped to the FFES physical fan output (`OUT7_STATE`)
- If your board wiring or controller configuration differs, these mappings may need adjustment

## Debug Logging

To enable debug logging, add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ffes_sauna: debug
    pymodbus: debug
```

## Support

- 🐛 [Report a Bug](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/issues)
- 💡 [Request a Feature](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/issues)
- 📖 [Documentation](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/wiki)

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FFES for providing Modbus documentation
- Home Assistant community for support and feedback
- PyModbus library maintainers

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## Development Status

### Home Assistant Brands Submission
- **Status**: Pending review
- **PR**: https://github.com/home-assistant/brands/pull/8326
- **Branch**: `patch-4` in fork https://github.com/LeszekWroblowski/brands
- **Updated**: 2025-11-02
- **Files submitted**:
  - icon.png (256×256, RGBA transparent)
  - icon@2x.png (512×512, RGBA transparent)
  - logo.png (256×128, RGBA transparent)
  - logo@2x.png (512×256, RGBA transparent)
- **Next step**: Wait for reviewer feedback. When response arrives, optionally add comment to PR:
  ```
  I've updated all brand assets with transparent backgrounds and correct dimensions:
  - icon.png (256×256)
  - icon@2x.png (512×512)
  - logo.png (256×128)
  - logo@2x.png (512×256)

  All files now have RGBA transparency as requested.
  ```

---

Made with ❤️ for the Home Assistant community
