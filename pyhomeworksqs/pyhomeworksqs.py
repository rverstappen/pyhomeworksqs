"""
Homeworks QS.

A partial implementation of an interface to Lutron Homeworks QS systems.

The interface is via telnet to a Lutron Homeworks QS repeater.

This project is largely based on 'pyhomeworks', by Michael Dubno.
"""

from threading import Thread
import time
import socket
import select
import logging

_LOGGER = logging.getLogger(__name__)

POLLING_FREQ = 1.
NEWLINE='\r'+'\n'

def _p_iid(arg):        return int(arg)
def _p_action(arg):     return int(arg)
def _p_param1(arg):     return arg
def _p_param2(arg):     return arg
def _p_param3(arg):     return arg
def _p_button(arg):     return int(arg)
def _p_address(arg):    return arg
def _p_enabled(arg):    return arg == 'enabled'
def _p_level(arg):      return float(arg)
def _p_ledstate(arg):   return [int(num) for num in arg]

def _norm(x):   return (x, _p_address, _p_button)
def _output(x): return (x, _p_iid, _p_action, _p_button)


# Callback types
HW_OUTPUT_ACTION_IGNORED = 'ignored_action'
HW_OUTPUT_ACTION_ZONE_LEVEL = 'zone_level'
HW_DEVICE_DISABLE = 'device_disable'
HW_DEVICE_DOUBLE_TAP = 'button_double_tap'
HW_DEVICE_ENABLE = 'device_enable'
HW_DEVICE_HOLD = 'button_hold'
HW_DEVICE_PRESS = 'button_press'
HW_DEVICE_RELEASE = 'button_release'
#HW_KEYPAD_ENABLE_CHANGED = 'keypad_enable_changed'
#HW_KEYPAD_LED_CHANGED = 'keypad_led_changed'
#HW_LIGHT_CHANGED = 'light_changed'

OUTPUT_ACTIONS = {
    1:	(HW_OUTPUT_ACTION_ZONE_LEVEL,    _p_iid, _p_param1, _p_param2),
#    2:	(HW_START_RISING,         _p_iid),
#    3:	(HW_START_LOWERING,       _p_iid),
#    4:	(HW_STOP_RISING_LOWERING, _p_iid),
    29:	(HW_OUTPUT_ACTION_IGNORED,       _p_iid, _p_param1, _p_param2),
    30:	(HW_OUTPUT_ACTION_IGNORED,       _p_iid, _p_param1, _p_param2),
}

DEVICE_ACTIONS = {
    1:	_norm(HW_DEVICE_ENABLE),
    2:	_norm(HW_DEVICE_DISABLE),
    3:	_norm(HW_DEVICE_PRESS),
    4:	_norm(HW_DEVICE_RELEASE),
    5:	_norm(HW_DEVICE_HOLD),
    6:	_norm(HW_DEVICE_DOUBLE_TAP),
}

NULL_ACTIONS = {}

COMMANDS = {
    "~OUTPUT": OUTPUT_ACTIONS,
    "~DEVICE": DEVICE_ACTIONS,
    "~MONITORING": NULL_ACTIONS,
}
#   (HW_OUTPUT_ACTION, _p_iid, _p_action, _p_param1, _p_param2, _p_param3),
#    "~MONITORING": (HW_IGNORED_INFO, _p_param1, _p_param2, _p_param3),
#    "KBP":      _norm(HW_BUTTON_PRESSED),
#    "KBR":      _norm(HW_BUTTON_RELEASED),
#    "KBH":      _norm(HW_BUTTON_HOLD),
#    "KBDT":     _norm(HW_BUTTON_DOUBLE_TAP),
#    "KLS":      (HW_KEYPAD_LED_CHANGED, _p_address, _p_ledstate),
#    "DL":       (HW_LIGHT_CHANGED, _p_address, _p_level),
#    "KES":      (HW_KEYPAD_ENABLE_CHANGED, _p_address, _p_enabled),
#}


class HomeworksQs(Thread):
    """Interface with a Lutron Homeworks QS system."""

    def __init__(self, host, port, callback):
        """Connect to controller using host, port."""
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._login = "lutron"
        self._password = "integration"
        self._callback = callback
        self._socket = None

        self._running = False
        self._connect()
        if self._socket == None:
            raise ConnectionError("Couldn't connect to '%s:%d'" % (host, port))
        self.start()

    def _connect(self):
        try:
            self._socket = socket.create_connection((self._host, self._port))
            _LOGGER.info("Connected to %s:%d", self._host, self._port)
        except (BlockingIOError, ConnectionError, TimeoutError) as error:
            pass

    def _send(self, command):
        _LOGGER.debug("send: %s", command)
        try:
            self._socket.send((command+NEWLINE).encode('utf8'))
            return True
        except (ConnectionError, AttributeError):
            self._socket = None
            return False

    def set_dimmer_level(self, iid, intensity, fade_time, delay_time):
        """Change the dim-level of an output."""
        self._send('#OUTPUT,%d,1,%.1f,%d' %
                   (iid, intensity, fade_time))

    def request_dimmer_level(self, iid):
        """Request the controller to return brightness."""
        self._send('?OUTPUT,%d' % iid)

    def request_configuration(self):
        """Request QS controller to send complete configuration (large XML string)."""
        self._send('?SYSTEM, 12')
#                        elif msg_buffer.startswith('<?xml'):
#                            _LOGGER.info("Got some XML.")
#                            xml_bulk = True
#                            pos = msg_buffer.rfind('>\r\n')
#                            if pos > 0:
#                                self.handleXmlConfig(msg_buffer[:pos+1])
#                                msg_buffer = msg_buffer[pos+4,len(msg_buffer)]
#                                xml_bulk = False

    def run(self):
        """Read and dispatch messages from the controller."""
        self._running = True
        msg_buffer = ""
        while self._running:
            if self._socket == None:
                time.sleep(POLLING_FREQ)
                self._connect()
            else:
                try:
                    _LOGGER.info("waiting on select()")
                    readable, _, _ = select.select([self._socket], [], [], POLLING_FREQ)
                    if len(readable) != 0:
                        chunks = []
                        bytes_recd = 0
                        while bytes_recd < len(readable):
                            chunk = self._socket.recv(2048)
                            chunks.append(chunk.decode('utf-8'))
                            bytes_recd += len(chunk)
                        msg_buffer += ''.join(chunks)
                        _LOGGER.debug("msg_buffer begins (%d): %s", len(msg_buffer), msg_buffer[:100])
                        if msg_buffer == 'login: ':
                            self._send(self._login)
                            msg_buffer = ''
                        elif msg_buffer == 'password: ':
                            self._send(self._password)
                            msg_buffer = ''
                        elif msg_buffer == '\r\nQNET> \x00':
                            _LOGGER.info("Found first QNET prompt; disabling prompt")
                            self._send('#MONITORING,12,2')
                            msg_buffer = ''
                        else:
                            # we may have multiple reponses spearated by \r\n
                            pos = msg_buffer.rfind('\r\n')
                            if pos > 0:
                                msgs = msg_buffer[:pos]
                                _LOGGER.debug("Found complete msg(s): %s", msgs)
                                for msg in msgs.split('\r\n'):
                                    if len(msg) > 0:
                                        _LOGGER.debug("Processing msg: %s", msg)
                                        self._processReceivedData(msg)
                                msg_buffer = msg_buffer[pos+2:]
                                
                except (ConnectionError, AttributeError):
                    _LOGGER.warning("Lost connection.")
                    self._socket = None
                except UnicodeDecodeError:
                    msg_buffer = ""

    def _processReceivedData(self, data):
        _LOGGER.debug("raw msg (len=%d): %s", len(data), data[0:100])
        try:
            raw_args = data.split(',')
            command = COMMANDS.get(raw_args[0], None)
            if command == OUTPUT_ACTIONS:
                _LOGGER.debug("raw_args[1]: %s, raw_args[2]: %s", raw_args[1], raw_args[2])
                iid = _p_iid(raw_args[1])
                action = OUTPUT_ACTIONS.get(_p_action(raw_args[2]))
                _LOGGER.debug("IID: %d, Action: %s", iid, action)
                if iid and action:
                    if len(raw_args)-1 <= len(action):
                        args = [parser(arg) for parser, arg in
                                zip(action[2:], raw_args[2:])]
                        self._callback(action[0], iid, args)
                    else:
                        _LOGGER.debug("Not handling (1a): %s", raw_args)
                else:
                    _LOGGER.debug("Not handling (2a): %s", raw_args)
            elif command == DEVICE_ACTIONS:
                iid = _p_iid(raw_args[1])
                action = DEVICE_ACTIONS.get(_p_action(raw_args[2]))
                _LOGGER.debug("IID: %d, Action: %s", iid, action)
                if iid and action:
                    if len(raw_args)-1 <= len(action):
                        args = [parser(arg) for parser, arg in
                                zip(action[2:], raw_args[2:])]
                        self._callback(action[0], iid, args)
                    else:
                        _LOGGER.debug("Not handling (1b): %s", raw_args)
                else:
                    _LOGGER.debug("Not handling (2b): %s", raw_args)
            else:
                _LOGGER.debug("Not handling (3): %s", raw_args)
        except ValueError:
            _LOGGER.warning("Weird data: %s", data)

    def close(self):
        """Close the connection to the controller."""
        self._running = False
        if self._socket:
            time.sleep(POLLING_FREQ)
            self._socket.close()
            self._socket = None
