
from psychopy import core, visual, event

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

    win = visual.Window(size=(1200, 1200), units='height')

    circ = visual.Circle(win, radius=0.01, edges=64, fillColor='white')

    target = visual.Circle(win, radius=0.02, fillColor='red', pos=(0.3, 0.2))
    dev = MpDevice(TestSerial())
    with dev:
        while not event.getKeys():
            data = dev.read()
            if data is not None:
                # map to -0.5, 0.5
                data = data[-1].astype('f') # voltage [0, 2^8]
                data /= 2**12 # normalized voltage [0, 1]
                data *= 0.5 # normalized voltage [0, 0.5]
                data[0] *= -1
                data[2] *= -1
                net_data = data[0] + data[3], data[1] + data[2]
                circ.pos = net_data
            target.draw()
            circ.draw()
            win.flip()
