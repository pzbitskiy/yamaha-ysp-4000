"""YSP4000 serial interface commands and responses"""
from abc import abstractmethod, ABC
from enum import Enum
from typing import Dict, Callable, List, Optional, Tuple


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
    STX = b'\x02'
    ETX = b'\x03'
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
        return ReadyCommand.CMD


class ControlCommandBase(ABC):  # pylint: disable=too-few-public-methods
    """Base control command for state changing"""
    @staticmethod
    def control_cmd(sw: bytes, data: bytes) -> bytes:  # pylint: disable=invalid-name
        """Constructs control cmd"""
        return YspSerialCodes.STX.value + sw + data + YspSerialCodes.ETX.value


class SystemCommand(YspCommandIf, ControlCommandBase):
    """Ysp4000 system command"""

    @staticmethod
    def cmd(**kwargs) -> Optional[bytes]:
        if (volume := kwargs.get('volume')) is not None:
            return ControlCommandBase.control_cmd(b'8', b'38' + volume)
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
                '6': b'B6',  # dock
                '7': b'7D',  # xm
            }
            if (cmd := input_map.get(input_val)) is not None:
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif volume := kwargs.get('volume'):
            cmd = b'1E' if volume > 0 else b'1F' if volume < 0 else None  # up or down
            if cmd is not None:
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif (power := kwargs.get('power')):
            power_map = {
                'on':      b'7E',
                'off':     b'7F',
                'standby': b'7F',
            }
            if cmd := power_map.get(power.lower()):
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

        elif (dsp := kwargs.get('dsp')):
            dsp_map = {
                'spectacle':    b'F9',
                'sci-fi':       b'FA',
                'adventure':    b'FB',
                'movie':        b'FB',   # default movie/cinema
                'cinema':       b'FB',  # default movie/cinema
                'concert':      b'E1',
                'concert hall': b'E1',
                'jazz':         b'EC',
                'jazz club':    b'EC',
                'sport':        b'F8',
                'sports':       b'F8',
            }
            extra = {}
            for key, val in dsp_map.items():
                if '-' in key:
                    extra[key.replace('-', ' ')] = val
                    extra[key.replace('-', '_')] = val
                if ' ' in key:
                    extra[key.replace(' ', '-')] = val
                    extra[key.replace(' ', '_')] = val
                if '_' in key:
                    extra[key.replace('_', ' ')] = val
                    extra[key.replace('_', '-')] = val
            if extra:
                dsp_map.update(extra)

            if cmd := dsp_map.get(dsp.lower()):
                return ControlCommandBase.control_cmd(b'0', b'7E' + cmd)
            if dsp.lower() in ('off', 'disable'):
                return ControlCommandBase.control_cmd(b'0', b'789B')

        elif (beam := kwargs.get('beam')):
            beam_map = {
                '5beam':  b'C2',
                '3beam':  b'C4',
                'stereo': b'50',
            }
            if cmd := beam_map.get(beam.lower()):
                return ControlCommandBase.control_cmd(b'0', b'78' + cmd)

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
        self.buf += data[:i+1]
        remaining = data[i+1:]

        if complete:
            # parse the entire buffer
            pos = 0
            for key, value in self.layout().items():
                size, handler = value
                if len(self.buf) < pos+size:
                    break
                elem = self.buf[pos:pos+size]
                pos += size
                self.fields[key] = elem
                if handler:
                    handler(elem)

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

    DT8_POWER = 8
    DT9_INPUT = 9
    DT12_VOLUME_HIGH_NIBBLE = 12
    DT14_VOLUME_LOW_NIBBLE = 13

    def __init__(self):
        super().__init__()
        self.power: Optional[str] = None
        self.input: Optional[str] = None
        self.volume: Optional[str] = None

        _ = None
        self.cmd_layout = {
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
        ysp.update_state(power=self.power, input=self.input,
                         volume=self.volume)

    def _parse_len(self, data: bytes):
        """Parse variable len field"""
        data_len = int(data, 16)
        existing = self.cmd_layout['data']
        self.cmd_layout['data'] = (data_len, existing[1])

    def _parse_data(self, data: bytes):
        """Parse DT items"""
        if len(data) > self.DT8_POWER:
            power = data[self.DT8_POWER]
            if power == ord(b'0'):
                self.power = 'off'
            if power == ord(b'1'):
                self.power = 'on'
        if len(data) > self.DT9_INPUT:
            # 0: TV/STB / 1: DVD / 2: AUX1 / 3: AUX2 / 4: AUX3 / 5 :DOCK / 6 :FM / 7 :XM
            self.input = chr(data[self.DT9_INPUT])
        if len(data) > self.DT14_VOLUME_LOW_NIBBLE:
            high = chr(data[self.DT12_VOLUME_HIGH_NIBBLE])
            low = chr(data[self.DT14_VOLUME_LOW_NIBBLE])
            self.volume = high + low


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
            status_map = {
                b'00': 'ok',
                b'01': 'busy',
                b'02': 'standby',
            }
            if status := status_map.get(rdata):
                kwargs['status'] = status

        elif rcmd == b'01':
            kwargs['status'] = 'warning'

        elif rcmd == b'20':
            power_map = {
                b'00': 'off',
                b'01': 'on',
            }
            if power := power_map.get(rdata):
                kwargs['power'] = power

        elif rcmd == b'21':
            # 0: TV/STB / 1: DVD / 2: AUX1 / 3: AUX2 / 4: AUX3 / 5 :DOCK / 6 :FM / 7 :XM
            kwargs['input'] = chr(rdata[1])

        elif rcmd == b'26':
            high = chr(rdata[0])
            low = chr(rdata[1])
            kwargs['volume'] = high + low

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
