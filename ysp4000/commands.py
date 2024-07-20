"""YSP4000 serial interface commands and responses"""
from abc import abstractmethod, ABC
from enum import Enum
import logging
from typing import Dict, Callable, List, Optional, Tuple

# Also seen these responses, support?
# startup: system playback report b'\x02301009\x03' b'\x02301100\x03' b'\x02301001\x03'
# power off incomplete b'\x0210200\x10  b'\x0210200\x00
# power on: b'\x02102001\x03'


logger = logging.getLogger('cmd')


class YspStateUpdatableIf(ABC):  # pylint: disable=too-few-public-methods
    """Ysp4000 interface for state updates declared here for typing support"""
    @abstractmethod
    def update_state(self, **kwargs):
        """update internal state"""


class YspResponseHandlerIf(ABC):
    """Ysp400 response handler interface"""
    @abstractmethod
    def match(self, data: bytes) -> bool:
        """Checks if data suitable for this handler"""

    @abstractmethod
    def consume(self, data: bytes) -> Optional[bytes]:
        """Consumes as many bytes from data and returns remaining"""

    @abstractmethod
    def done(self) -> bool:
        """Returns True if response fully parsed"""

    @abstractmethod
    def emit_changes(self, ysp: YspStateUpdatableIf):
        """updates Ysp4000 with a state learned from the response"""


class YspSerialCodes(Enum):
    """Common serial command start/end codes"""
    NUL = b'\x00'
    STX = b'\x02'
    ETX = b'\x03'
    DLE = b'\x10'
    DC1 = b'\x11'
    DC2 = b'\x12'
    DC3 = b'\x13'


class YspCommandIf(ABC):  # pylint: disable=too-few-public-methods
    """Ysp400 input command"""
    @staticmethod
    @abstractmethod
    def cmd(**kwargs) -> Optional[bytes]:
        """Return bytes for sending to serial port.
        None value indicates there is no command for such arguments
        """


class ReadyCommand(YspCommandIf):  # pylint: disable=too-few-public-methods
    """Ready command used to initiate communication session"""
    CMD = YspSerialCodes.DC1.value + b'\x00\x00\x00' + YspSerialCodes.ETX.value

    @staticmethod
    def cmd(**kwargs) -> Optional[bytes]:
        logger.debug('ready cmd: %s', ReadyCommand.CMD)
        return ReadyCommand.CMD


class ControlCommandBase(ABC):  # pylint: disable=too-few-public-methods
    """Base control command for state changing"""
    @staticmethod
    def control_cmd(sw: bytes, data: bytes) -> bytes:  # pylint: disable=invalid-name
        """Constructs control cmd"""
        cmd = YspSerialCodes.STX.value + sw + data + YspSerialCodes.ETX.value
        logger.debug('control cmd: %s', cmd)
        return cmd


class SystemCommand(YspCommandIf, ControlCommandBase):
    """Ysp4000 system command"""

    @staticmethod
    def cmd(volume: str = None, **kwargs) -> Optional[bytes]:
        if volume is not None:
            return ControlCommandBase.control_cmd(b'8', b'30' + volume.encode())
        # others are not supported => noop
        return None


class OperationCommand(YspCommandIf, ControlCommandBase):
    """Ysp4000 system command"""

    @staticmethod
    def cmd(**kwargs: Dict[str, str]) -> Optional[bytes]:  # pylint: disable=too-many-branches,too-many-return-statements
        if input_val := kwargs.get('input'):
            # 0: TV/STB / 1: DVD / 2: AUX1 / 3: AUX2 / 4: AUX3 / 5 :DOCK / 6 :FM / 7 :XM
            input_map = {
                '0': b'DF',  # tv
                '1': b'4A',  # dvd
                '2': b'49',  # aux1
                '3': b'DE',  # aux2
                '4': b'BC',  # aux3
                '6': b'B6',  # fm
                '7': b'7D',  # xm
                '8': b'4B',  # fm
            }
            if (cmd := input_map.get(input_val)) is not None:
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif volume := kwargs.get('volume'):
            cmd = b'1E' if volume > 0 else b'1F' if volume < 0 else None  # up or down
            if cmd is not None:
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif (power := kwargs.get('power')):
            power_map = {
                '0': b'7F',  # off
                '1': b'7E',  # on
            }
            if cmd := power_map.get(power.lower()):
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif (program := kwargs.get('program')):
            # 0: Cinema DSP Off / 1: Movie Sci-Fi / 2: Movie Spectacle / 3: Movie Adventure
            # 4: Music Video / 5: Music Concert Hall / 6:Music Jazz Club / 7:Sports
            program_map = {
                '1': b'FA',
                '2': b'F9',
                '3': b'FB',
                '4': b'F3',
                '5': b'E1',
                '6': b'EC',
                '7': b'F8',
            }
            if cmd := program_map.get(program):
                return ControlCommandBase.control_cmd(b'0', b'7E' + cmd)
            if program.lower() in ('0', 'off', 'disable'):
                return ControlCommandBase.control_cmd(b'0', b'789B')

        elif (beam := kwargs.get('beam')):
            # 0: 5Beam / 1: ST+3Beam / 2: 3Beam / 3: Stereo / 4: Target
            beam_map = {
                '0': b'C2',
                '1': b'C3',
                '2': b'C4',
                '3': b'50',
                '5': b'C5',  # my beam
                '6': b'C6',  # my surround
            }
            if cmd := beam_map.get(beam):
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)
            if cmd == '4':  # 5ch stereo
                return ControlCommandBase.control_cmd(b'0', b'7EFF')

        return None


class YspResponseBase(YspResponseHandlerIf):
    """Base class for Ysp400 response parsing"""

    def __init__(self):
        self.buf = b''
        self.fields = {}
        self.completed = False

    @abstractmethod
    def start_byte(self) -> int:
        """Returns a byte indicating command start"""

    @abstractmethod
    def end_byte(self) -> int:
        """Returns a byte indicating command end"""

    @abstractmethod
    def layout(self) -> Dict[str, Tuple[int, Optional[Callable]]]:
        """Returns cmd layout"""

    def consume(self, data: bytes) -> Optional[bytes]:
        if not self.buf:
            self.fields: Dict[str, bytes] = {}
            self.completed = False
            assert data[0] == self.start_byte()

        complete = False
        i = 0
        remaining = data
        for i, val in enumerate(data):
            if val == self.end_byte():
                complete = True
                break
            if val in (ord(YspSerialCodes.NUL.value), ord(YspSerialCodes.DLE.value)):
                # this is incomplete response to power off looks like
                complete = True
                break
        self.buf += data[:i+1]
        remaining = data[i+1:]

        if complete:
            logger.debug('parsed cmd: %s', self.buf)
            # parse the entire buffer
            pos = 0
            for key, value in self.layout().items():
                size: int = None
                handler: Callable[[bytes, bytes], None] = None
                size, handler = value
                if len(self.buf) < pos+size:
                    logger.debug('incomplete: exp %d, got %d bytes',
                                 pos + size, len(self.buf))
                    break
                elem = self.buf[pos:pos+size]
                pos += size
                self.fields[key] = elem
                if handler:
                    handler(self.buf, elem)

            self.buf = b''
            self.completed = True

        return remaining

    def match(self, data: bytes) -> bool:
        return data[0] == self.start_byte()

    def done(self) -> bool:
        return self.completed


class ConfigurationCommand(YspResponseBase):
    """Ready command response parser (YSP configuration command)"""
    START_BYTE = YspSerialCodes.DC2.value
    END_BYTE = YspSerialCodes.ETX.value

    DT7_SYSTEM = 7
    DT8_POWER = 8
    DT9_INPUT = 9
    DT12_VOLUME_HIGH = 12
    DT13_VOLUME_LOW = 13
    DT14_PROGRAM = 14
    DT29_BEAM = 29

    def __init__(self):
        super().__init__()
        self.status: Optional[str] = None
        self.power: Optional[str] = None
        self.input: Optional[str] = None
        self.volume: Optional[str] = None
        self.program: Optional[str] = None
        self.beam: Optional[str] = None

        _ = None
        self.cmd_layout: Dict[str, Tuple[int, Callable[[bytes, bytes], None]]] = {
            'start': (1, _),
            'type':  (5, _),
            'ver':   (1, _),
            'len':   (2, self._parse_len),
            'data':  (0, self._parse_data),  # set by _parse_len
            'sum':   (2, _),
            'end':   (1, _),
        }

    def start_byte(self) -> bytes:
        return ord(self.START_BYTE)

    def end_byte(self) -> bytes:
        return ord(self.END_BYTE)

    def layout(self) -> Dict[str, Tuple[int, Optional[Callable]]]:
        return self.cmd_layout

    def emit_changes(self, ysp: YspStateUpdatableIf):
        ysp.update_state(
            status=self.status,
            power=self.power,
            input=self.input,
            volume=self.volume,
            program=self.program,
            beam=self.beam,
        )

    def _parse_len(self, buf: bytes, chunk: bytes):
        """Parse variable len field"""
        data_len = int(chunk, 16)
        existing = self.cmd_layout['data']
        self.cmd_layout['data'] = (data_len, existing[1])

        # max documented data is 145 bytes but YSP400 might report data size = 147
        total = sum(val[0] for val in self.cmd_layout.values())
        if total > len(buf):
            max_data_len = 144
            logger.debug(
                'config cmd fixup: %d > %d: %d -> %d', total, len(buf), data_len, max_data_len)
            self.cmd_layout['data'] = (max_data_len, existing[1])

    def _parse_data(self, _: bytes, chunk: bytes):
        """Parse DT items"""
        if len(chunk) > self.DT7_SYSTEM:
            # 0: OK / 1: Busy / 2: P-Off
            self.status = chr(chunk[self.DT7_SYSTEM])
        if len(chunk) > self.DT8_POWER:
            # 0: Off / 1: On
            self.power = chr(chunk[self.DT8_POWER])
        if len(chunk) > self.DT9_INPUT:
            # 0: TV/STB / 1: DVD / 2: AUX1 / 3: AUX2 / 4: AUX3 / 5 :DOCK / 6 :FM / 7 :XM
            self.input = chr(chunk[self.DT9_INPUT])
        if len(chunk) > self.DT13_VOLUME_LOW:
            self.volume = chunk[self.DT12_VOLUME_HIGH: self.DT13_VOLUME_LOW+1].decode()
        if len(chunk) > self.DT14_PROGRAM:
            # 0: Cinema DSP Off / 1: Movie Sci-Fi / 2: Movie Spectacle / 3: Movie Adventure
            # 4: Music Video / 5: Music Concert Hall / 6:Music Jazz Club / 7:Sports
            self.program = chr(chunk[self.DT14_PROGRAM])
        if len(chunk) > self.DT29_BEAM:
            # 0: 5Beam / 1: ST+3Beam / 2: 3Beam / 3: Stereo / 4: Target
            self.beam = chr(chunk[self.DT29_BEAM])


class ReportCommand(YspResponseBase):
    """Control command response parser (YSP report command)"""
    START_BYTE = YspSerialCodes.STX.value
    END_BYTE = YspSerialCodes.ETX.value

    def __init__(self):
        super().__init__()

        _ = None
        self.cmd_layout = {
            'start': (1, _),
            'type':  (1, _),
            'guard': (1, _),
            'rcmd':  (2, _),
            'rdata': (2, _),
            'end':   (1, _),
        }

    def start_byte(self) -> bytes:
        return ord(self.START_BYTE)

    def end_byte(self) -> bytes:
        return ord(self.END_BYTE)

    def layout(self) -> Dict[str, Tuple[int, Optional[Callable]]]:
        return self.cmd_layout

    def emit_changes(self, ysp: YspStateUpdatableIf):
        rcmd: bytes = self.fields['rcmd']
        rdata: bytes = self.fields['rdata']

        kwargs: Dict[str, str] = {}
        # system cmd response
        if rcmd == b'00':
            kwargs['status'] = chr(rdata[1])

        elif rcmd == b'01':
            kwargs['status'] = 'warning'

        elif rcmd == b'20':
            if rdata[1] >= ord('0'):
                kwargs['power'] = chr(rdata[1])
            else:
                # handle incomplete cmd with rdata = b'0\x10', b'0\x00' by forcing to off
                kwargs['power'] = '0'

        elif rcmd == b'21':
            kwargs['input'] = chr(rdata[1])

        elif rcmd == b'26':
            kwargs['volume'] = rdata.decode()

        elif rcmd == b'28':
            kwargs['program'] = chr(rdata[0])
            # surround = chr(rdata[1])

        elif rcmd == b'B0':
            kwargs['beam'] = chr(rdata[1])

        ysp.update_state(**kwargs)


class ResponseParser:  # pylint: disable=too-few-public-methods
    """Serial port data parser from Ysp4000"""

    def __init__(self, ysp: YspStateUpdatableIf, handlers: List[YspResponseHandlerIf]):
        self.ysp = ysp
        self.handlers = handlers

        self.current = None

    def consume(self, data: bytes):
        """Consume raw data and orchestrate parsing"""
        def resume(data):
            data = self.current.consume(data)
            if self.current.done():
                self.current.emit_changes(self.ysp)
                self.current = None
            elif data:
                raise RuntimeError(
                    f'incomplete handler {self.current} has not consumed all data')
            return data

        if self.current:
            data = resume(data)
            if not data:
                return
        i = 0
        while i < len(self.handlers):
            handler = self.handlers[i]
            if handler.match(data):
                self.current = handler
                data = resume(data)
                if not data:
                    return
                # some data remaining, restart
                i = 0
            else:
                i += 1


def make_response_parser(ysp: YspStateUpdatableIf) -> ResponseParser:
    """Creates ResponseParser with all supported response handlers"""
    return ResponseParser(ysp, handlers=[ConfigurationCommand(), ReportCommand()])
