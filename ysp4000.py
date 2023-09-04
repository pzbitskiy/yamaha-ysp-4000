import logging
import time

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
        self.on = False
        self.status()

    def status(self):
        data = self._communicate(b'\x11\x00\x00\x00\x03', YSP4000.STATUS_CMD_SIZE, throw=False)
        # When the power is OFF, only DT0,1,…,9 are sent to the Host.
        # not true for YSP-4000 but...
        self.on = data is not None and len(data) > (9+10+3)
        if self.on:
            self.dt_data = data[1+8:-3]

    def close(self):
        self.ser.close()

    def _communicate(self, cmd, expect_bytes, throw=True):
        logging.debug('sending cmd: %s', cmd)
        result = b''
        for i in range(2):
            self.ser.write(cmd)
            time.sleep(0.1)
            remaining = expect_bytes
            data = self.ser.read(expect_bytes)
            while len(data) > 0 and remaining > 0:
                logging.debug('recv: %s', data)
                result += data
                remaining -= len(data)
                if remaining == 0:
                    break
                data = self.ser.read(remaining)
            if len(result) > 0:
                break
        else:
            if throw:
                raise 'Cannot connect to YSP-4000: no response'
            result = None

        return result


    def set_input_tv(self):
        if self.get_input() == YSP4000.INPUT_TV:
            return
        self._communicate(b'\x02078DF\x03', 8*7)  # 7 report commands

    def set_input_aux1(self):
        if self.get_input() == YSP4000.INPUT_AUX1:
            return
        self._communicate(b'\x0207849\x03', 8*7)

    def power_off(self):
        if not self.on:
            return
        self._communicate(b'\x020787F\x03', 8)  # powering off YSP-4000 breaks data transmission so it could return 1-8 bytes

    def power_on(self):
        if self.on:
            return
        data = self._communicate(b'\x020787E\x03', 8 + YSP4000.STATUS_CMD_SIZE + 3 * 8)  # report + status data + 3 reports
        self.dt_data = data[8+1+8:-(3+3*8)] # skip first and last report commands

    def raw_dt(self):
        return self.dt_data

    def get_input(self):
        return self.dt_data[YSP4000.DT9_INPUT_STATUS]

def main():
    try:
        ysp = YSP4000()
        ysp.power_on()
        ysp.set_input_aux1()
        print(ysp.raw_dt())
        # ysp.set_input_tv()
        # ysp.power_off()

    finally:
        ysp.close()


if __name__ == '__main__':
    main()

