"""
Demo platform that offers a fake climate device.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/demo/
"""
import voluptuous as vol
from homeassistant.components.climate import (
    ClimateDevice,
    DOMAIN,
    PLATFORM_SCHEMA,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_FAN_MODE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_ON_OFF,

    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_OPERATION_MODE,
    ATTR_FAN_MODE,
    ATTR_OPERATION_LIST,
    ATTR_FAN_LIST

)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE,
    ATTR_ENTITY_ID,
    CONF_VALUE_TEMPLATE,
    ATTR_FRIENDLY_NAME
)

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['websockets==6.0']

ATTR_ANUS_MODE = "anus_mode"


SET_ANUS_MODE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_ANUS_MODE): cv.boolean,
})

SERVICE_SET_ANUS_MODE = 'set_anus_mode'

import sys
sys.path.insert(0, "/home/per/IdeaProjects/savecair")
from savecair import SaveCair


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    climate =  DemoClimate(config["name"], config["unit"], config["iam_id"], config["password"])
    """Set up the Demo climate devices."""
    async_add_entities([climate])


class DemoClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, name, unit, iam_id, password):
        self._name = name


        """Initialize the climate device."""
        self._support_flags = SUPPORT_TARGET_TEMPERATURE

        if unit == "vtr_300":
            self._support_flags = self._support_flags | SUPPORT_FAN_MODE  # OFF, LOW, MEDIUM, HIGH
            self._support_flags = self._support_flags | SUPPORT_OPERATION_MODE  # Heat, cool. etc ? kan brukes som mode?
            self._support_flags = self._support_flags | SUPPORT_ON_OFF

        # Create savecair client
        self._client = SaveCair(iam_id, password)
        self._client.update_cb.append(self.update_callback)

        self._fan_list = ['Off', 'Low', 'Normal', 'High']
        self._operation_list = ['Auto', 'Manual', 'Crowded', 'Refresh', 'Fireplace', 'Away', 'Holiday']

    def update_callback(self):
        self.schedule_update_ha_state()

    async def async_update(self):
        """Retrieve latest state."""
        await self._client.update_sensors()
        self.schedule_update_ha_state()

    async def async_service_anus_mode(entity, service):
        print("YEYSYSYS")

    @property
    def state_attributes(self):
         # Return the device specific state attributes.
        return {
            ATTR_FAN_MODE: self.current_fan_mode,
            ATTR_CURRENT_TEMPERATURE: self.current_temperature,
            ATTR_TEMPERATURE: self.target_temperature,
            ATTR_FAN_LIST: self.fan_list,
            ATTR_CURRENT_HUMIDITY: self.current_humidity,
            ATTR_OPERATION_MODE: self.current_operation,
            ATTR_OPERATION_LIST: self.operation_list,
            ATTR_FRIENDLY_NAME: self.name,
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""

        if "control_regulation_temp_unit" not in self._client.data:
            return TEMP_CELSIUS

        if self._client.data["control_regulation_temp_unit"] == "celsius":
            return TEMP_CELSIUS
        else:
            return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._client.data["supply_air_temp"] / 10 if "supply_air_temp" in self._client.data else None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._client.data["main_temperature_offset"] / 10 if "main_temperature_offset" in self._client.data else None

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._client.data["rh_sensor"] if "rh_sensor" in self._client.data else None

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        if "main_airflow" not in self._client.data:
            return None
        else:
            return self._fan_list[int(self._client.data["main_airflow"]) - 1]

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if "main_user_mode" not in self._client.data:
            return None
        else:
            return self._operation_list[int(self._client.data["main_user_mode"])]

    @property
    def is_on(self):
        """Return true if the device is on."""

        if "main_airflow" not in self._client.data:
            return True
        else:
            if int(self._client.data["main_airflow"]) - 1 > 0:
                return True
            else:
                return False

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        if self.current_operation is "Manual":
            return self._fan_list
        return None

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        self.hass.async_create_task(self._client.set_temperature(temperature))

    def set_fan_mode(self, fan_mode):
        """Set new target temperature."""
        if fan_mode == "Off":
            self.hass.async_create_task(self._client.set_fan_off())
        elif fan_mode == "Low":
            self.hass.async_create_task(self._client.set_fan_low())
        elif fan_mode == "Normal":
            self.hass.async_create_task(self._client.set_fan_normal())
        elif fan_mode == "Maximum":
            self.hass.async_create_task(self._client.set_fan_high())

    def set_operation_mode(self, operation_mode):

        if operation_mode == "Auto":
            self.hass.async_create_task(self._client.set_auto_mode())
        elif operation_mode == "Manual":
            self.hass.async_create_task(self._client.set_manual_mode())
        elif operation_mode == "Crowded":
            self.hass.async_create_task(self._client.set_crowded_mode())
        elif operation_mode == "Refresh":
            self.hass.async_create_task(self._client.set_refresh_mode())
        elif operation_mode == "Fireplace":
            self.hass.async_create_task(self._client.set_fireplace_mode())
        elif operation_mode == "Away":
            self.hass.async_create_task(self._client.set_away_mode())
        elif operation_mode == "Holiday":
            self.hass.async_create_task(self._client.set_holiday_mode())

    def turn_on(self):
        # Turn on
        self.hass.async_create_task(self._client.set_fan_high())

    def turn_off(self):
        # Turn off
        self.hass.async_create_task(self._client.set_manual_mode())
        self.hass.async_create_task(self._client.set_fan_off())