# -*- coding: utf-8 -*-


import sys
import glob

import serial
import serial.tools.list_ports as tools


BAUDRATES = [
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "115200"
        ]


def serial_ports():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def find_ports():
    return [info.device for info in tools.comports()]


START_OUT = [s.encode('utf-8') for s in ('$', 'C', 'M')]
CS_OUT = [(12).to_bytes(1, byteorder='big')]
END_OUT = [s.encode('utf-8') for s in ('\r', '\n')]



class Model:
    def __init__(self):
        pass

    def configure(self, pparam, mparam, vparam):
        self._pparam = pparam
        self._mparam = mparam
        self._vparam = vparam

        self.serobj = serial.Serial(port=self._pparam['name'],
                                    baudrate=self._pparam['baudrate'],
                                    timeout=1)

        self.message = self.generate()

    def disconnect(self):
        if self.serobj.is_open:
            self.serobj.close()

    def send(self, vparam):
        self._vparam = vparam
        self.message = self.generate()

        for byte_ in self.message:
            self.serobj.write(byte_)

    def generate(self):
        data = self._mparam['channels'] * [self._vparam['other']['value']]

        for channel, value in zip(self._vparam['custom']['channel'], self._vparam['custom']['value']):
            data[channel - 1] = value

        data_bytes = []
        for index, item in enumerate(data):
            num = (index + 1).to_bytes(1, byteorder='big')
            bytes_ = (item).to_bytes(2, byteorder='big', signed=True)
            data_bytes.extend([num, bytes_])

        length = (self._mparam['channels']).to_bytes(1, byteorder='big')

        if self._mparam['channels_byte']:
            message = START_OUT + [length] + data_bytes + CS_OUT + END_OUT
        else:
            message = START_OUT + data_bytes + CS_OUT + END_OUT

        print(message)
        return message
