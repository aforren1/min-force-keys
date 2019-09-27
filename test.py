import struct
from ctypes import c_uint16
import serial
from serial.tools import list_ports
from toon.input import MpDevice, BaseDevice, Obs
from time import sleep

class TestSerial(BaseDevice):
    class Pos(Obs):
        shape = (4,)
        ctype = c_uint16

    def __init__(self, nonblocking=False, **kwargs):
        super(TestSerial, self).__init__(**kwargs)
        self.nonblocking = nonblocking
        self._device = None

    def enter(self):
        ports = list_ports.comports()
        mydev = next((p.device for p in ports if p.pid == 1155))
        self._device = serial.Serial(mydev)
        self._device.close()
        sleep(0.5)
        self._device.open()
        return self

    def exit(self, *args):
        self._device.close()

    def read(self):
        data = self._device.read(64)
        time = self.clock()
        if data:
            data = struct.unpack('<' + 'H' * 4, bytearray(data[:8]))
            return self.Returns(pos=self.Pos(time, data))
        else:
            return None, None

if __name__ == '__main__':
    from timeit import default_timer
    dev = MpDevice(TestSerial())
    with dev:
        t1 = default_timer() + 5
        while default_timer() < t1:
            data = dev.read()
            if data is not None:
                print(data)
