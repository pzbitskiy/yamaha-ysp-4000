import logging
import time
import sys

import serial

logging.basicConfig(level=logging.INFO)

class YSP4000:
    STATUS_CMD_SIZE = 1+8+144+2+1
    DT9_INPUT_STATUS = 9
    INPUT_TV = '0'
    INPUT_AUX1 = '2'

    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1)

        self.dt_data = None
        self.on = None
        self.input = None

    def _ready(func):
        def wrapper(self, *args, **kwargs):
            if self.dt_data is None:
                self.dt_data = self._status()
                logging.debug('calling %s: DT: %s', func.__name__, self.dt_data)
            func(self, *args, **kwargs)
        return wrapper

    def _status(self):
        data = self._communicate(b'\x11\x00\x00\x00\x03', YSP4000.STATUS_CMD_SIZE, throw=False)
        # When the power is OFF, only DT0,1,…,9 are sent to the Host.
        # not true for YSP-4000 but...
        self.on = data is not None and len(data) > (9+10+3)
        dt_data = data[1+8:-3] if self.on else None
        logging.debug('power state: %s', self.on)
        return dt_data

    def close(self):
        self.ser.close()

    def _communicate(self, cmd, expect_bytes, throw=True):
        logging.debug('sending cmd: %s', cmd)
        result = b''
        for i in range(5):
            self.ser.write(cmd)
            time.sleep(0.1)
            remaining = expect_bytes
            extra = 0
            data = self.ser.read(expect_bytes)
            while len(data) > 0:
                logging.debug('recv: %s', data)
                result += data
                remaining -= len(data)
                if remaining <= 0:
                    data = self.ser.read(8)
                    if not data:
                        break
                    extra += len(data)
                else:
                    data = self.ser.read(remaining)
            if extra > 0:
                logging.debug('expected %d but read %d (%d extra)', expect_bytes, len(result), extra)
            if len(result) < expect_bytes:
                logging.debug('expected %d but read %d', expect_bytes, len(result))

            if len(result) > 0:
                break
        else:
            if throw:
                raise Exception('Cannot connect to YSP-4000: no response')
            result = None

        return result

    @_ready
    def set_input_tv(self):
        if self.get_input() == YSP4000.INPUT_TV:
            return
        data = self._communicate(b'\x02078DF\x03', 8*8)  # 8 report commands
        self.input = YSP4000.INPUT_TV
        return data

    @_ready
    def set_input_aux1(self):
        if self.get_input() == YSP4000.INPUT_AUX1:
            return
        data = self._communicate(b'\x0207849\x03', 8*8)
        self.input = YSP4000.INPUT_AUX1
        return data

    @_ready
    def volume_up(self):
        return self._communicate(b'\x020781E\x03', 8)

    @_ready
    def volume_down(self):
        return self._communicate(b'\x020781F\x03', 8)

    @_ready
    def set_dsp_cinema(self):
        return self._communicate(b'\x0207EFB\x03', 8)

    @_ready
    def set_dsp_music(self):
        self._communicate(b'\x0207EE1\x03', 8)

    @_ready
    def set_dsp_off(self):
        self._communicate(b'\x020789B\x03', 8)

    @_ready
    def set_3beam(self):
        self._communicate(b'\x02078C4\x03', 3*8)

    @_ready
    def set_5beam(self):
        self._communicate(b'\x02078C2\x03', 3*8)

    @_ready
    def set_stereo(self):
        self._communicate(b'\x0207850\x03', 3*8)

    @_ready
    def power_off(self):
        if not self.on:
            return
        self._communicate(b'\x020787F\x03', 8)  # powering off YSP-4000 breaks data transmission so it could return 1-8 bytes
        self.on = False
        self.dt_data = None

    @_ready
    def power_on(self):
        if self.on:
            return
        data = self._communicate(b'\x020787E\x03', 8 + YSP4000.STATUS_CMD_SIZE + 3 * 8)  # report + status data + 3 reports
        self.dt_data = data[8+1+8:-(3+3*8)] # skip first and last report commands
        self.on = True
        return data

    def raw_dt(self):
        return self.dt_data

    def get_input(self):
        if not self.input:
            self.input = self.dt_data[YSP4000.DT9_INPUT_STATUS]
        return self.input


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ('-d', '--debug', '-v', '--verbose'):
            logging.basicConfig(level=logging.DEBUG, force=True)

    try:
        ysp = YSP4000()
        ysp.power_on()
        # ysp.set_input_aux1()
        # ysp.set_dsp_cinema()
        # ysp.set_5beam()
        ysp.set_3beam()
        ysp.set_dsp_music()
        ysp.volume_up()
        # print(ysp.raw_dt())
        ysp.set_input_tv()
        ysp.power_off()

    finally:
        ysp.close()


if __name__ == '__main__':
    main()

