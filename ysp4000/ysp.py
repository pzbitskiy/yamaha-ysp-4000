"""YSP4000 Serial controller"""
import asyncio
import logging
from typing import Callable, Coroutine, Dict, Optional, TypeAlias

import serial
import serial_asyncio

from ysp4000.commands import make_response_parser, ReadyCommand, OperationCommand, SystemCommand
from ysp4000.hfn import make_hfn_mapper, BeamMap, InputMap, PowerMap, ProgramMap, \
    ReportMap, StatusMap, VolumeMap


def init_logging(level=None, **kwargs):
    """init logging"""
    if not level:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
        **kwargs)


logger = logging.getLogger('ysp')


Ysp4000TypeAlias: TypeAlias = 'Ysp4000'

class Ysp4000:  # pylint: disable=too-many-instance-attributes
    """Yamaha YSP4000 serial controller"""
    class Decorators:  # pylint: disable=too-few-public-methods
        """Defines internal decorators"""
        @staticmethod
        def ready(func):
            """Ysp ready decorator ensures YSP4000 is ready to communicate by
            synchronously sending a ready command.
            """
            def wrapper(self: Ysp4000TypeAlias, *args, **kwargs):
                # pylint: disable=protected-access
                if not self._ready:
                    logger.debug('not ready...')
                    self.ser_transport.pause_reading()
                    self.communicate(ReadyCommand.cmd())
                    self.ser_transport.resume_reading()
                    logger.debug('calling %s', func.__name__)
                    self._write_cmd(SystemCommand.cmd(report=ReportMap.enable))
                func(self, *args, **kwargs)
            return wrapper

    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        callback: Callable = None,
        verbose: Optional[bool] = None
    ):

        self.state: Dict[str: Optional[str]] = {
            'status':  None,
            'power':   None,
            'input':   None,
            'volume':  None,
            'program': None,
            'beam':    None,
        }

        # start without opening a port
        self._port = port
        self._ser = serial.Serial(
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

        self._callback = callback
        self._response_parser = make_response_parser(self)
        self._hfn_mapper = make_hfn_mapper()

        self.ser_transport: Optional[asyncio.Protocol] = None
        self._ready: Optional[bool] = None

        if verbose:
            init_logging(level=logging.DEBUG, force=True)

    def get_async_coro(self, event_loop) -> Coroutine:
        """Return coroutine for serial port communication loop"""
        logger.info('starting coroutine on serial %s', self._port)
        self._ser.port = self._port
        self._ser.open()

        this = self

        class Protocol(asyncio.Protocol):
            """asyncio.Protocol for serial port, reads all data as they arrive"""

            def connection_made(self, transport):
                self.transport = transport  # pylint: disable=attribute-defined-outside-init
                this.ser_transport = transport

            def data_received(self, data):
                this._handle(data)          # pylint: disable=protected-access

        coroutine = serial_asyncio.connection_for_serial(
            event_loop, Protocol, self._ser)
        return coroutine

    def communicate(self, cmd: bytes):
        """Synchronously sends data to YSP4000 and parses result.
        At the moment used during
        initialization.
        """
        self._write_cmd(cmd)
        data = self.read_all()
        logger.debug('communicated: %s -> %s', cmd, data)
        self._response_parser.consume(data)

    def _write_cmd(self, cmd: Optional[bytes]):
        """Helper function that writes optional command to serial port"""
        if cmd:
            logger.debug('sending %s', cmd)
            self._ser.write(cmd)

    def _handle(self, data):
        """Protocol callback to handle data"""
        logger.debug('recv %s', data)
        self._response_parser.consume(data)

    def read_all(self) -> bytes:
        """Read all data from the port with 1s timeout and parses it updating its own state.
        This method should be used only when not running an event loop.
        Returns all data read.
        """
        timeout = self._ser.timeout
        self._ser.timeout = 1
        buf = b''
        while True:
            read = self._ser.read()
            if not read:
                break
            buf += read

        self._ser.timeout = timeout
        logger.debug('read all: %s', buf)
        self._response_parser.consume(buf)
        return buf

    @property
    def on(self) -> bool:
        """Returns True if YSP4000 is powered on"""
        return self.state['power'] == PowerMap.on

    @Decorators.ready
    def power_on(self):
        """Power on the device"""
        if self.on:
            return
        self._write_cmd(OperationCommand.cmd(power=PowerMap.on))

    @Decorators.ready
    def power_off(self):
        """Power off the device"""
        if not self.on:
            return
        self._write_cmd(OperationCommand.cmd(power=PowerMap.off))

    @Decorators.ready
    def set_5beam(self):
        """Set beam mode to 5Beam"""
        if self.state['beam'] != BeamMap.beam5:
            self._write_cmd(OperationCommand.cmd(beam=BeamMap.beam5))

    @Decorators.ready
    def set_3beam(self):
        """Set beam mode to 3Beam"""
        if self.state['beam'] != BeamMap.beam3:
            self._write_cmd(OperationCommand.cmd(beam=BeamMap.beam3))

    @Decorators.ready
    def set_stereo(self):
        """Set beam mode to stereo"""
        if self.state['beam'] != BeamMap.stereo:
            self._write_cmd(OperationCommand.cmd(beam=BeamMap.stereo_beam3))

    @Decorators.ready
    def set_input_tv(self):
        """Set input to TV"""
        if self.state['input'] != InputMap.tv:
            self._write_cmd(OperationCommand.cmd(input=InputMap.tv))

    @Decorators.ready
    def set_input_aux1(self):
        """Set input to AUX1"""
        if self.state['input'] != InputMap.aux1:
            self._write_cmd(OperationCommand.cmd(input=InputMap.aux1))

    @Decorators.ready
    def set_dsp_off(self):
        """Turn off DSP"""
        if self.state['program'] != ProgramMap.off:
            self._write_cmd(OperationCommand.cmd(program=ProgramMap.off))

    @Decorators.ready
    def set_dsp_cinema(self):
        """Set program to generic cinema"""
        if self.state['program'] != ProgramMap.adventure:
            self._write_cmd(OperationCommand.cmd(program=ProgramMap.adventure))

    @Decorators.ready
    def set_dsp_music(self):
        """Set program to music"""
        if self.state['program'] != ProgramMap.concert:
            self._write_cmd(OperationCommand.cmd(program=ProgramMap.concert))

    @Decorators.ready
    def set_volume_pct(self, value: int):
        """Set volume to 0-99 pct"""
        val: str = VolumeMap.convert_pct(value)
        logger.debug('set volume: %d(%s)', value, val)
        self._write_cmd(SystemCommand.cmd(volume=val))

    @Decorators.ready
    def set_volume(self, value: str):
        """Set volume to absolute value 00-EE"""
        logger.debug('set volume: %s', value)
        self._write_cmd(SystemCommand.cmd(volume=value))

    @Decorators.ready
    def volume_up(self):
        """Increment volume by 3 pct"""
        current = self.state.get('volume', '00')
        value = min(int(VolumeMap().code_to_hfn(current)) + 3, 100)
        self.set_volume_pct(value)

    @Decorators.ready
    def volume_down(self):
        """Increment volume by 3 pct"""
        current = self.state.get('volume', '00')
        value = max(int(VolumeMap().code_to_hfn(current)) - 3, 0)
        self.set_volume_pct(value)

    def update_state(self, **kwargs):
        """Update state"""
        updates = {}
        for key, new in kwargs.items():
            old = self.state.get('key')
            if old != new:
                self.state[key] = new
                updates[key] = self._hfn_mapper(key, new)
            if key == 'status' and new == StatusMap.ok:
                self._ready = True

        if updates:
            logger.debug('state updated: %s', updates)

        if self._callback is not None:
            self._callback(**updates)

    def close(self):
        """close the serial port"""
        self._ser.close()
