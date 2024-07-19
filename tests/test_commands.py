"""Command parsing tests"""
import random
from typing import Any, Callable
import unittest

from ysp4000.commands import ConfigurationCommand, ReportCommand, \
    make_response_parser


def whole_feeder(data: bytes, func: Callable, assertion: Any, no_remainder: bool=None) -> bytes:  # pylint: disable=unused-argument
    """Calls func with the entre data chunk"""
    return func(data)


def byte_feeder(data: bytes, func: Callable, assertion: Any, no_remainder: bool=None) -> bytes:
    """Calls func with one byte chunks"""
    rem = None
    for i in range(len(data)):
        rem = func(data[i:i+1])
        if no_remainder:
            assertion.assertFalse(rem)
    return rem


def random_feeder(data: bytes, func: Callable, assertion: Any, no_remainder: bool=None) -> bytes:
    """Calls func with random size chunks"""
    rem = None
    i = 0
    while i < len(data):
        size = random.randint(1, 4)
        size = min(size, len(data)-i)
        rem = func(data[i:i+size])
        if no_remainder:
            assertion.assertFalse(rem)
        i += size
    return rem


class MockUpdatable:  # pylint: disable=too-few-public-methods
    """Mock class emulating ysp state update"""

    def __init__(self):
        self.kwargs = {}

    def update_state(self, **kwargs):
        """update state callback"""
        self.kwargs.update(kwargs)


READY_RESP_POWERED_OFF = b'\x12G0079D09@E0190000A3\x03'
READY_RESP_POWERED_ON = b'\x12G0079D93@E01900010009E70040100001818100202A2A222D2D280000222A2A28' + \
    b'2A2A222A2A28282828285A011411E1410000044050005050575181818181800000050505050010101000010A3\x03'

OP_RESP_VOLUME_CHANGE1 = b'\x021026B2\x03'
OP_RESP_VOLUME_CHANGE2 = b'\x021026A6\x03'


class TestCommandsParsing(unittest.TestCase):
    """Test individual command parsing"""

    def test_ready(self):
        """Test ready command response parsing"""

        def run(data: bytes, data2: bytes, feeder: Callable):
            handler = ConfigurationCommand()
            self.assertTrue(handler.match(data))
            self.assertTrue(handler.match(data[0:1]))

            # data = handler.consume(data) with splitting
            remainder = feeder(data, handler.consume, self, no_remainder=True)

            self.assertFalse(remainder)
            self.assertTrue(handler.done())
            ysp = MockUpdatable()
            handler.emit_changes(ysp)
            self.assertEqual(ysp.kwargs['power'], 'off')
            self.assertIsNone(ysp.kwargs['input'])
            self.assertIsNone(ysp.kwargs['volume'])

            # data2
            self.assertTrue(handler.match(data2))
            self.assertTrue(handler.match(data2[0:1]))

            remainder = feeder(data2, handler.consume, self, no_remainder=True)

            self.assertFalse(remainder)
            self.assertTrue(handler.done())
            ysp = MockUpdatable()
            handler.emit_changes(ysp)
            self.assertEqual(ysp.kwargs['power'], 'on')
            self.assertEqual(ysp.kwargs['input'], '0')
            self.assertEqual(ysp.kwargs['volume'], '9E')

        random.seed(None)
        run(READY_RESP_POWERED_OFF, READY_RESP_POWERED_ON, whole_feeder)
        run(READY_RESP_POWERED_OFF, READY_RESP_POWERED_ON, byte_feeder)
        run(READY_RESP_POWERED_OFF, READY_RESP_POWERED_ON, random_feeder)

    def test_report(self):
        """Test operation command response parsing"""

        def run(data: bytes, data2: bytes, feeder: Callable):
            handler = ReportCommand()
            self.assertTrue(handler.match(data))
            self.assertTrue(handler.match(data[0:1]))

            # data = handler.consume(data) with splitting
            remainder = feeder(data, handler.consume, self, no_remainder=True)

            self.assertFalse(remainder)
            self.assertTrue(handler.done())
            ysp = MockUpdatable()
            handler.emit_changes(ysp)
            self.assertEqual(len(ysp.kwargs), 1)
            self.assertEqual(ysp.kwargs['volume'], 'B2')

            # ensure it can parse two commands in a row
            self.assertTrue(handler.match(data2))
            self.assertTrue(handler.match(data2[0:1]))

            # data = handler.consume(data) with splitting
            remainder = feeder(data2, handler.consume, self, no_remainder=True)

            self.assertFalse(remainder)
            self.assertTrue(handler.done())
            ysp = MockUpdatable()
            handler.emit_changes(ysp)
            self.assertEqual(len(ysp.kwargs), 1)
            self.assertEqual(ysp.kwargs['volume'], 'A6')

        random.seed(None)
        run(OP_RESP_VOLUME_CHANGE1, OP_RESP_VOLUME_CHANGE2, whole_feeder)
        run(OP_RESP_VOLUME_CHANGE1, OP_RESP_VOLUME_CHANGE2, byte_feeder)
        run(OP_RESP_VOLUME_CHANGE1, OP_RESP_VOLUME_CHANGE2, random_feeder)

    def test_partial_resume(self):
        """Test command response handles partial commands and resumes"""
        part1 = READY_RESP_POWERED_ON[:30]
        part2 = READY_RESP_POWERED_ON[30:] + OP_RESP_VOLUME_CHANGE1[:4]
        part3 = OP_RESP_VOLUME_CHANGE1[4:]

        ysp = MockUpdatable()
        handler = ConfigurationCommand()
        remainder = handler.consume(part1)
        self.assertFalse(remainder)
        self.assertEqual(len(ysp.kwargs), 0)

        remainder = handler.consume(part2)
        self.assertTrue(remainder)
        self.assertTrue(handler.done())
        handler.emit_changes(ysp)
        self.assertGreater(len(ysp.kwargs), 0)
        # ensure configuration part parsed
        self.assertEqual(ysp.kwargs['power'], 'on')
        self.assertEqual(ysp.kwargs['input'], '0')
        self.assertEqual(ysp.kwargs['volume'], '9E')

        handler = ReportCommand()
        remainder = handler.consume(remainder + part3)
        self.assertFalse(remainder)
        self.assertTrue(handler.done())
        handler.emit_changes(ysp)
        # ensure volume part parsed
        self.assertEqual(ysp.kwargs['power'], 'on')
        self.assertEqual(ysp.kwargs['input'], '0')
        self.assertEqual(ysp.kwargs['volume'], 'B2')


class TestResponseParser(unittest.TestCase):
    """Test ResponseParser class"""
    def test_single(self):
        """Test ResponseParser handles single commands"""
        def run1(data: bytes, feeder: Callable):
            ysp = MockUpdatable()
            parser = make_response_parser(ysp)
            remainder = feeder(data, parser.consume, self, no_remainder=True)
            self.assertFalse(remainder)
            self.assertEqual(len(ysp.kwargs), 1)
            self.assertEqual(ysp.kwargs['volume'], 'B2')

        random.seed(None)
        run1(OP_RESP_VOLUME_CHANGE1, whole_feeder)
        run1(OP_RESP_VOLUME_CHANGE1, byte_feeder)
        run1(OP_RESP_VOLUME_CHANGE1, random_feeder)


        def run2(data: bytes, feeder: Callable):
            ysp = MockUpdatable()
            parser = make_response_parser(ysp)
            remainder = feeder(data, parser.consume, self, no_remainder=True)
            self.assertFalse(remainder)
            self.assertEqual(ysp.kwargs['power'], 'on')
            self.assertEqual(ysp.kwargs['input'], '0')
            self.assertEqual(ysp.kwargs['volume'], '9E')

        random.seed(None)
        run2(READY_RESP_POWERED_ON, whole_feeder)
        run2(READY_RESP_POWERED_ON, byte_feeder)
        run2(READY_RESP_POWERED_ON, random_feeder)

    def test_stream(self):
        """Test ResponseParser handles multiple commands"""

        def run(data: bytes, feeder: Callable):
            ysp = MockUpdatable()
            parser = make_response_parser(ysp)
            remainder = feeder(data, parser.consume, self, no_remainder=True)
            self.assertFalse(remainder)
            # self.assertEqual(len(ysp.kwargs), 1)
            self.assertEqual(ysp.kwargs['power'], 'on')
            self.assertEqual(ysp.kwargs['input'], '0')
            self.assertEqual(ysp.kwargs['volume'], 'B2')

        random.seed(None)
        cmd = READY_RESP_POWERED_OFF + READY_RESP_POWERED_ON + OP_RESP_VOLUME_CHANGE1
        run(cmd, whole_feeder)
        run(cmd, byte_feeder)
        run(cmd, random_feeder)

    def test_partial_resume(self):
        """Test ResponseParser handles partial commands and resumes"""
        part1 = READY_RESP_POWERED_ON[:30]
        part2 = READY_RESP_POWERED_ON[30:] + OP_RESP_VOLUME_CHANGE1[:4]
        part3 = OP_RESP_VOLUME_CHANGE1[4:]

        ysp = MockUpdatable()
        parser = make_response_parser(ysp)
        remainder = parser.consume(part1)
        self.assertFalse(remainder)
        self.assertEqual(len(ysp.kwargs), 0)

        remainder = parser.consume(part2)
        self.assertFalse(remainder)  # no remainder, parser consumes as much as it can
        self.assertGreater(len(ysp.kwargs), 0)
        # check only POWER_ON portion updated
        self.assertEqual(ysp.kwargs['power'], 'on')
        self.assertEqual(ysp.kwargs['input'], '0')
        self.assertEqual(ysp.kwargs['volume'], '9E')

        remainder = parser.consume(part3)
        self.assertFalse(remainder)
        # check the remaining VOLUME portion is updated as well
        self.assertEqual(ysp.kwargs['power'], 'on')
        self.assertEqual(ysp.kwargs['input'], '0')
        self.assertEqual(ysp.kwargs['volume'], 'B2')
