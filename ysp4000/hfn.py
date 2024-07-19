"""Human friendly names for YSP400 codes"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional

# pylint: disable=too-few-public-methods

class MapperIf(ABC):
    """Mapper interface"""
    @abstractmethod
    def code_to_hfn(self, code: str) -> str:
        """Returns friendly name for a code"""

class ProgramMap(MapperIf):
    """Program codes to human-friendly names mapping
    0: Cinema DSP Off / 1: Movie Sci-Fi / 2: Movie Spectacle / 3: Movie Adventure
    4: Music Video / 5: Music Concert Hall / 6:Music Jazz Club / 7:Sports
    """

    FRIENDLY_NAMES = {
        'DSP off':            '0',
        'Movie Sci-Fi':       '1',
        'Movie Spectacle':    '2',
        'Movie Adventure':    '3',
        'Music Video':        '4',
        'Music Concert Hall': '5',
        'Music Jazz Club':    '6',
        'Sports':             '7',
    }

    ALIASES = {
        'sci-fi':       '1',
        'spectacle':    '2',
        'adventure':    '3',
        'movie':        '3',
        'cinema':       '3',
        'music clip':   '4',
        'music':        '4',
        'clip':         '4',
        'concert':      '5',
        'concert hall': '5',
        'jazz':         '6',
        'jazz club':    '6',
        'sport':        '7',
    }

    def __init__(self):
        extra = {}
        for key, val in self.ALIASES.items() + self.FRIENDLY_NAMES.items():
            key: str = key.lower()
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
            self.ALIASES.update(extra)

        self.code_to_name: Dict[str, str] = {}
        for key, val in self.FRIENDLY_NAMES.items():
            self.code_to_name[val] = key

    def code_to_hfn(self, code: str) -> str:
        return self.code_to_name.get(code)


class PowerMap(MapperIf):
    """Power codes to human-friendly names mapping
    0: Off / 1: On
    """
    FRIENDLY_NAMES = {
        'Off': '0',
        'On':  '1',
    }

    def __init__(self):
        self.code_to_name: Dict[str, str] = {}
        for key, val in self.FRIENDLY_NAMES.items():
            self.code_to_name[val] = key

    def code_to_hfn(self, code: str) -> str:
        return self.code_to_name.get(code)


class StatusMap(MapperIf):
    """Power codes to human-friendly names mapping
    0: OK / 1: Busy / 2: P-Off (Standby)
    """
    FRIENDLY_NAMES = {
        'OK':      '0',
        'Busy':    '1',
        'Standby': '2',
    }

    def __init__(self):
        self.code_to_name: Dict[str, str] = {}
        for key, val in self.FRIENDLY_NAMES.items():
            self.code_to_name[val] = key

    def code_to_hfn(self, code: str) -> str:
        return self.code_to_name.get(code)


class BeamMap(MapperIf):
    """Beam codes to human-friendly names mapping
    0: 5Beam / 1: ST+3Beam / 2: 3Beam / 3: Stereo / 4: Target
    """
    FRIENDLY_NAMES = {
        '5Beam':       '0',
        'ST+3Beam':    '1',
        '3Beam':       '2',
        'Stereo':      '3',
        '5ch Stereo':  '4',
        'My Beam':     '5',
        'My Surround': '6',
    }

    def __init__(self):
        self.code_to_name: Dict[str, str] = {}
        for key, val in self.FRIENDLY_NAMES.items():
            self.code_to_name[val] = key

    def code_to_hfn(self, code: str) -> str:
        return self.code_to_name.get(code)


class InputMap(MapperIf):
    """Input source codes to human-friendly names mapping
    0: TV/STB / 1: DVD / 2: AUX1 / 3: AUX2 / 4: AUX3 / 5 :DOCK / 6 :FM / 7 :XM / 8 :DAB
    """
    FRIENDLY_NAMES = {
        'TV/STB': '0',
        'DVD':    '1',
        'AUX1':   '2',
        'AUX2':   '3',
        'AUX3':   '4',
        'DOCK':   '5',
        'FM':     '6',
        'XM':     '7',
        'DAB':    '8',
    }

    def __init__(self):
        self.code_to_name: Dict[str, str] = {}
        for key, val in self.FRIENDLY_NAMES.items():
            self.code_to_name[val] = key

    def code_to_hfn(self, code: str) -> str:
        return self.code_to_name.get(code)


class VolumeMap(MapperIf):
    """Volume converter"""
    def __init__(self):
        pass

    def code_to_hfn(self, code: str) -> str:
        pass


def make_hfn_mapper() -> Callable[[str, str], Optional[str]]:
    """Returns human friendly mapper callable"""
    mappers: Dict[str, MapperIf] = {
        'status':  StatusMap(),
        'power':   PowerMap(),
        'input':   InputMap(),
        'volume':  VolumeMap(),
        'program': ProgramMap(),
        'beam':    BeamMap(),
    }
    def mapper(key: str, code: str) -> Optional[str]:
        mapper = mappers.get(key)
        if not mapper:
            return None
        return mapper.code_to_hfn(code)

    return mapper
