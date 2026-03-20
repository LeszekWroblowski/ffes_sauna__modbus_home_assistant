"""Constants for the FFES Sauna integration."""
from typing import Final

DOMAIN: Final = "ffes_sauna"

# Configuration
CONF_SLAVE: Final = "slave"
DEFAULT_NAME: Final = "FFES Sauna"
DEFAULT_PORT: Final = 502
DEFAULT_SLAVE: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 10

# Modbus Register Offset
# FFES REG[1] starts at physical Modbus address 1 (not 0, not 2!)
# Physical address 1 = REG[1], physical address 2 = REG[2], etc.
REGISTER_OFFSET: Final = 1
REGISTER_COUNT: Final = 50  # Total number of registers available (REG[1] to REG[50])

# Modbus Register Addresses (REG[x] in documentation = address x-1)
# 1-bit registers (coils)
REG_CONTROLLER_STATE: Final = 0  # REG[1]
REG_SESSION_STATE: Final = 1  # REG[2]
REG_VENTILATION_STATE: Final = 2  # REG[3]
REG_OUT1_STATE: Final = 3  # REG[4]
REG_OUT2_STATE: Final = 4  # REG[5]
REG_OUT3_STATE: Final = 5  # REG[6]
REG_OUT4_STATE: Final = 6  # REG[7]
REG_OUT5_STATE: Final = 7  # REG[8]
REG_OUT6_STATE: Final = 8  # REG[9]
REG_OUT7_STATE: Final = 9  # REG[10]
REG_WIFI_CONNECTION: Final = 39  # REG[40]
REG_SERVER_CONNECTION: Final = 40  # REG[41]
REG_PAIRING_MODE: Final = 41  # REG[42]
REG_FROST_PROTECTION: Final = 50  # REG[51]
REG_FROST_PROTECTION_STATUS: Final = 51  # REG[52]
REG_INFRARED_MIX_STATUS: Final = 52  # REG[53]
REG_INFRARED_MIX_MODE: Final = 53  # REG[54]
REG_SECOND_TEMP_FUNCTION_STATUS: Final = 55  # REG[56]

# 16-bit registers (holding)
REG_TEMPERATURE_SET: Final = 0  # REG[1]
REG_TEMPERATURE_ACTUAL: Final = 1  # REG[2]
REG_CLOCK: Final = 2  # REG[3]
REG_SAUNA_PROFILE: Final = 3  # REG[4]
REG_SESSION_TIME: Final = 4  # REG[5]
REG_VENTILATION_TIME: Final = 5  # REG[6]
REG_VAPORIZER_PREHEAT_TIME: Final = 6  # REG[7]
REG_AROMA_CYCLE_TIME: Final = 7  # REG[8]
REG_AROMA_SET_VALUE: Final = 8  # REG[9]
REG_VAPORIZER_HUMIDITY: Final = 9  # REG[10]
REG_ERROR_CODE: Final = 10  # REG[11]
REG_CPIR_GROUP_1_SET: Final = 11  # REG[12]
REG_CPIR_GROUP_2_SET: Final = 12  # REG[13]
REG_TEMP2_ACTUAL: Final = 13  # REG[14]
REG_HUMIDITY_ACTUAL: Final = 14  # REG[15]
REG_CONTROLLER_STATUS: Final = 19  # REG[20]
REG_MAIN_BOARD_SV: Final = 20  # REG[21]
REG_CPIR_G1_POWER: Final = 25  # REG[26]
REG_CPIR_G2_POWER: Final = 26  # REG[27]
REG_CPIR_G3_POWER: Final = 27  # REG[28]
REG_CPIR_G4_POWER: Final = 28  # REG[29]
REG_MODULE_SOFTWARE_VERSION: Final = 48  # REG[49]
REG_CONTROLLER_MODEL: Final = 49  # REG[50]

# Sauna Profiles
PROFILE_INFRARED: Final = 1
PROFILE_DRY_SAUNA: Final = 2
PROFILE_WET_SAUNA: Final = 3
PROFILE_VENTILATION: Final = 4
PROFILE_STEAM_BATH: Final = 5
PROFILE_INFRARED_CPIR: Final = 6
PROFILE_INFRARED_MIX: Final = 7

SAUNA_PROFILES: Final = {
    PROFILE_INFRARED: "infrared",
    PROFILE_DRY_SAUNA: "dry_sauna",
    PROFILE_WET_SAUNA: "wet_sauna",
    PROFILE_VENTILATION: "ventilation",
    PROFILE_STEAM_BATH: "steam_bath",
    PROFILE_INFRARED_CPIR: "infrared_cpir",
    PROFILE_INFRARED_MIX: "infrared_mix",
}

PROFILE_NAMES: Final = {
    "infrared": "Infrared Sauna",
    "dry_sauna": "Dry Sauna",
    "wet_sauna": "Wet Sauna",
    "ventilation": "Ventilation",
    "steam_bath": "Steam Bath",
    "infrared_cpir": "Infrared CPIR",
    "infrared_mix": "Infrared MIX",
}

PROFILE_NAME_TO_NUMBER: Final = {
    profile_name: profile_number
    for profile_number, profile_name in SAUNA_PROFILES.items()
}

# Controller model capability bits from FFES documentation (REG[50])
MODEL_IR: Final = 1 << 0
MODEL_HEATER: Final = 1 << 1
MODEL_STEAM_BATH: Final = 1 << 2
MODEL_WET: Final = 1 << 3
MODEL_AROMA: Final = 1 << 4
MODEL_FAN: Final = 1 << 5
MODEL_IR_CPIR: Final = 1 << 6

PROFILE_MODEL_MASKS: Final = {
    PROFILE_INFRARED: MODEL_IR,
    PROFILE_DRY_SAUNA: MODEL_HEATER,
    PROFILE_WET_SAUNA: MODEL_WET,
    PROFILE_VENTILATION: MODEL_FAN,
    PROFILE_STEAM_BATH: MODEL_STEAM_BATH,
    PROFILE_INFRARED_CPIR: MODEL_IR_CPIR,
}

# Controller Status Values
STATUS_OFF: Final = 0
STATUS_HEAT: Final = 1
STATUS_VENT: Final = 2
STATUS_STBY: Final = 3

STATUS_NAMES: Final = {
    STATUS_OFF: "Off",
    STATUS_HEAT: "Heating",
    STATUS_VENT: "Ventilation",
    STATUS_STBY: "Standby",
}

# Error Codes
ERROR_CODES: Final = {
    0: "No Error",
    1: "Temperature sensor disconnected or thermal fuse damaged",
    2: "Temperature exceeded maximum (125°C or 80°C for Wet/IR/Bath)",
    3: "Invalid temperature sensor reading",
    4: "Rapid temperature increase",
    5: "Low water level in heater tank",
    6: "Humidity sensor reading error",
    7: "Emergency switch active",
    8: "Door open too long during session",
    11: "CPIR module error L1",
    12: "CPIR module error L2",
    13: "CPIR module error L3",
}

# Temperature Limits by Profile
TEMP_LIMITS: Final = {
    PROFILE_INFRARED: {"min": 30, "max": 60},
    PROFILE_DRY_SAUNA: {"min": 30, "max": 110},
    PROFILE_WET_SAUNA: {"min": 30, "max": 65},
    PROFILE_VENTILATION: {"min": 0, "max": 0},  # Not applicable
    PROFILE_STEAM_BATH: {"min": 20, "max": 50},
    PROFILE_INFRARED_CPIR: {"min": 30, "max": 60},
    PROFILE_INFRARED_MIX: {"min": 30, "max": 60},
}

# Services
SERVICE_START_SESSION: Final = "start_session"
SERVICE_STOP_SESSION: Final = "stop_session"
SERVICE_SET_PROFILE: Final = "set_profile"

# Attributes
ATTR_PROFILE: Final = "profile"
ATTR_TEMPERATURE: Final = "temperature"
ATTR_DURATION: Final = "duration"
ATTR_HUMIDITY: Final = "humidity"
ATTR_ERROR_CODE: Final = "error_code"
ATTR_ERROR_MESSAGE: Final = "error_message"
ATTR_CONTROLLER_STATUS: Final = "controller_status"
ATTR_SOFTWARE_VERSION: Final = "software_version"
ATTR_MODEL: Final = "model"


def get_supported_profile_numbers(controller_model: int) -> list[int]:
    """Return the profile numbers supported by the controller model."""
    supported_profiles: list[int] = []

    for profile_number in (
        PROFILE_INFRARED,
        PROFILE_DRY_SAUNA,
        PROFILE_WET_SAUNA,
        PROFILE_VENTILATION,
        PROFILE_STEAM_BATH,
        PROFILE_INFRARED_CPIR,
    ):
        if controller_model & PROFILE_MODEL_MASKS[profile_number]:
            supported_profiles.append(profile_number)

    # Infrared MIX is available on hybrid controllers that expose both
    # the classic heater and the infrared subsystem.
    if controller_model & MODEL_HEATER and controller_model & MODEL_IR:
        supported_profiles.append(PROFILE_INFRARED_MIX)

    return supported_profiles
