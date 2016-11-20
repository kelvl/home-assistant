"""
Support for Broadlink Controller using python-broadlink
"""
import logging
import binascii
import broadlink

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_MAC, CONF_COMMAND_ON, CONF_COMMAND_OFF, CONF_SWITCHES, CONF_ID)
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    UNIT_NOT_RECOGNIZED_TEMPLATE,
    TEMPERATURE
)

import homeassistant.util.temperature

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

# DEPENDENCIES = ['broadlink']

_LOGGER = logging.getLogger(__name__)

CONF_KEY = 'key'

def vbytearray(value):
    if value is None:
        raise vol.Invalid('ByteArray should not be None')
    value = str(value)
    return bytearray(binascii.a2b_base64(value))

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_ID): vbytearray,
    vol.Required(CONF_KEY): vbytearray,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    host = config.get(CONF_HOST)
    port = 80
    mac = bytearray.fromhex(config.get(CONF_MAC))
    device = broadlink.device((host, port), mac)
    device.id = config.get(CONF_ID)
    device.key = config.get(CONF_KEY)

    _LOGGER.info("Broadlink Device %r %r %r %r", device.host, device.mac, device.id, device.key)

    devices = []

    temp_unit = hass.config.units.temperature_unit
    sensor = BroadlinkTemperatureSensor(device, 'broadlink', temp_unit)
    devices.append(sensor)

    add_devices(devices)

class BroadlinkTemperatureSensor(Entity):

    def __init__(self, device, name, temp_unit):
        self._device = device
        self._name = name
        self._temp_unit = temp_unit

        self.current_value = None

    @property
    def name(self):
        """Return the name of the temperature sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return TEMP_CELSIUS

    def update(self):
        """Retrieve latest state."""
        _LOGGER.info("Fetching temperature")
        celsius = self._device.check_temperature()
        if celsius < 100:
            _LOGGER.info("Got temperature: %r", celsius)
            self.current_value = celsius
