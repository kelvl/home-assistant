"""
Support for Broadlink Controller using python-broadlink
"""
import logging
import binascii
import broadlink

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_MAC, CONF_COMMAND_ON, CONF_COMMAND_OFF, CONF_SWITCHES, CONF_ID)
import homeassistant.helpers.config_validation as cv

# DEPENDENCIES = ['broadlink']

_LOGGER = logging.getLogger(__name__)

CONF_KEY = 'key'

def vbytearray(value):
    if value is None:
        raise vol.Invalid('ByteArray should not be None')
    value = str(value)
    return bytearray(binascii.a2b_base64(value))

SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_COMMAND_ON): vbytearray,
    vol.Required(CONF_COMMAND_OFF): vbytearray,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_ID): vbytearray,
    vol.Required(CONF_KEY): vbytearray,
    vol.Required(CONF_SWITCHES, default={}):
        vol.Schema({cv.string: SWITCH_SCHEMA}),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Arduino platform."""
    conf_switches = config.get(CONF_SWITCHES)
    host = config.get(CONF_HOST)
    port = 80
    mac = bytearray.fromhex(config.get(CONF_MAC))
    device = broadlink.device((host, port), mac)
    device.id = config.get(CONF_ID)
    device.key = config.get(CONF_KEY)

    _LOGGER.info("Broadlink Device %r %r %r %r", device.host, device.mac, device.id, device.key)

    devices = []
    for name, items in conf_switches.items():
        devices.append(BroadlinkSwitch(device, name, items[CONF_COMMAND_ON], items[CONF_COMMAND_OFF]))

    add_devices(devices)

class BroadlinkSwitch(SwitchDevice):
    def __init__(self, device, name, command_on, command_off):
        self._name = name
        self._on = command_on
        self._off = command_off
        self._state = False
        self._device = device

    @property
    def name(self):
        return self._name

    @property
    def assumed_state(self):
        return True

    @property
    def should_poll(self):
        """No polling needed for a broadlink switch."""
        return False

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.info('Switching %s on', self._name)
        self._state = True
        self._device.send_data(self._on)
        self.update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.info('Switching %s off', self._name)
        self._state = False
        self._device.send_data(self._off)
        self.update_ha_state()
