# Installation Guide - FFES Sauna Modbus Integration

This guide will walk you through the complete installation process.

## Prerequisites

Before you begin, make sure you have:

✅ Home Assistant installed (version 2024.1.0 or newer)  
✅ FFES Sauna controller with Modbus TCP support  
✅ Controller firmware 1.21/6.21 or newer  
✅ Controller connected to your local network  
✅ Controller IP address (e.g., 192.168.0.208)  
✅ HACS (Home Assistant Community Store) installed  

## Installation Methods

Choose one of the following installation methods:

### Method 1: HACS Installation (Recommended) ⭐

1. **Open HACS**
   - In Home Assistant, go to: HACS → Integrations

2. **Add Custom Repository**
   - Click the ⋮ menu (three dots) in the top right corner
   - Select "Custom repositories"
   - Add this repository URL: `https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant`
   - Category: Select "Integration"
   - Click "Add"

3. **Install Integration**
   - Search for "FFES Sauna" in HACS
   - Click on it
   - Click "Download"
   - Select the latest version
   - Click "Download" again

4. **Restart Home Assistant**
   - Go to: Settings → System → Restart
   - Wait for Home Assistant to restart (~30-60 seconds)

### Method 2: Manual Installation

1. **Download Files**
   - Download the latest release from GitHub
   - Or download `ffes-sauna-modbus.zip`

2. **Extract and Copy**
   ```bash
   # Extract the ZIP file
   unzip ffes-sauna-modbus.zip
   
   # Copy to Home Assistant
   cp -r ffes-sauna-modbus/custom_components/ffes_sauna /config/custom_components/
   ```

3. **Verify Structure**
   Your directory should look like:
   ```
   /config/custom_components/ffes_sauna/
   ├── __init__.py
   ├── manifest.json
   ├── config_flow.py
   ├── coordinator.py
   ├── climate.py
   ├── light.py
   ├── sensor.py
   ├── switch.py
   ├── number.py
   ├── select.py
   ├── binary_sensor.py
   ├── const.py
   ├── services.yaml
   ├── strings.json
   └── translations/
       ├── en.json
       └── pl.json
   ```

4. **Restart Home Assistant**
   - Settings → System → Restart

## Configuration

### Step 1: Verify Controller Connection

Before configuring, test the connection:

```bash
# Ping the controller
ping 192.168.0.208

# Test Modbus connection (optional, requires modbus tools)
mbpoll -m tcp -a 1 192.168.0.208 -t 3 -r 0 -c 1
```

### Step 2: Add Integration

1. **Navigate to Integrations**
   - Settings → Devices & Services
   - Click "+ Add Integration"

2. **Search for FFES Sauna**
   - Type "FFES" in the search box
   - Click on "FFES Sauna Modbus"

3. **Enter Configuration**
   Fill in the form:
   
   | Field | Value | Notes |
   |-------|-------|-------|
   | **IP Address** | `192.168.0.208` | Your controller's IP |
   | **Port** | `502` | Default Modbus TCP port |
   | **Slave ID** | `1` | Usually 1, check manual if unsure |
   | **Name** | `My Sauna` | Any friendly name |
   | **Scan Interval** | `10` | How often to update (5-120 seconds) |

4. **Submit**
   - Click "Submit"
   - Wait for validation
   - If successful, you'll see "Success!" message

### Step 3: Verify Installation

Check that entities were created:

1. **Go to Devices**
   - Settings → Devices & Services
   - Click on "FFES Sauna"
   - You should see your device

2. **Check Entities**
   You should see approximately 27-32 entities, depending on controller model:
   - ✅ 1 Climate (thermostat)
   - ✅ 11 Sensors (temperature, humidity, status, etc.)
   - ✅ 5 Switches (power, ventilation, fan output, etc.)
   - ✅ 1 Light (sauna light output)
   - ✅ 8 Numbers (session time, aromatherapy, etc.)
   - ✅ 1 Select (profile selector filtered by controller capabilities)
   - ✅ 5 Binary Sensors (error, heating, etc.)

3. **Test Basic Control**
   - Developer Tools → Services
   - Try calling: `switch.turn_on` on `switch.my_sauna_power`
   - Check if sauna responds

## Troubleshooting

### Problem: Integration Not Found

**Solution:**
- Verify files are in `/config/custom_components/ffes_sauna/`
- Check file permissions (should be readable)
- Restart Home Assistant again
- Check logs: Settings → System → Logs

### Problem: Cannot Connect

**Possible Causes:**

1. **Wrong IP Address**
   ```bash
   # Test connection
   ping 192.168.0.208
   ```

2. **Port Blocked**
   - Check firewall settings
   - Verify port 502 is open
   - Try from different device on same network

3. **Modbus Not Enabled**
   - Check controller settings
   - Verify Modbus TCP is enabled
   - Consult controller manual

4. **Wrong Slave ID**
   - Default is 1
   - Try values: 0, 1, 255
   - Check controller documentation

### Problem: Entities Not Updating

**Solution:**
- Increase scan interval (try 30 seconds)
- Check logs for Modbus errors
- Verify no other device is using Modbus simultaneously
- Verify that the selected profile is supported by your controller model

### Problem: Read/Write Errors

**Enable Debug Logging:**

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.ffes_sauna: debug
    pymodbus: debug
```

Restart and check logs.

## Post-Installation

### 1. Create Dashboard

Add a card to your dashboard. See `example_configuration.yaml` for examples.

### 2. Set Up Automations

Create your first automation:
```yaml
automation:
  - alias: "Start Sauna at 6 PM"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: ffes_sauna.start_session
        target:
          entity_id: climate.my_sauna_thermostat
        data:
          profile: 2
          temperature: 85
          duration: 60
```

### 3. Configure Notifications

Get notified when sauna is ready:
```yaml
automation:
  - alias: "Sauna Ready"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_sauna_current_temperature
        above: 80
    action:
      - service: notify.mobile_app
        data:
          message: "Sauna is ready! 🧖"
```

### 4. Test All Features

Go through this checklist:
- [ ] Turn sauna on/off
- [ ] Change temperature
- [ ] Select different profiles
- [ ] Set session time
- [ ] Control aromatherapy
- [ ] Test ventilation
- [ ] Test sauna light
- [ ] Test physical fan output
- [ ] Check error monitoring
- [ ] Try services (start_session, stop_session)

## Notes About Profiles and Outputs

- The integration reads `REG[50]` (`CONTROLLER_MODEL`) and only exposes profiles supported by your controller
- `light.my_sauna_light` is mapped to the FFES light output (`OUT3_STATE`)
- `switch.my_sauna_fan_output` is mapped to the FFES physical fan output (`OUT7_STATE`)
- If your hardware wiring differs, these output mappings may need to be adjusted

## Next Steps

📖 Read the [README.md](README.md) for full documentation  
🚀 Check [QUICK_START.md](QUICK_START.md) for quick tips  
📝 See [example_configuration.yaml](example_configuration.yaml) for automation ideas  
💬 Join discussions on GitHub  
⭐ Star the project if you find it useful!  

## Support

Need help?

- 🐛 [Report bugs](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/issues)
- 💬 [Ask questions](https://github.com/LeszekWroblowski/ffes_sauna__modbus_home_assistant/discussions)
- 📧 Check controller manual for Modbus settings

## Version Check

Verify your installation:

```yaml
# In Developer Tools → Template
{{ state_attr('sensor.my_sauna_software_version', 'state') }}
```

Should show your controller firmware version.

---

**Installation Complete! Enjoy your smart sauna! 🎉🧖‍♂️**
