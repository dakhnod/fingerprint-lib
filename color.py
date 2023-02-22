import serial
import time

class Controller():
    def __init__(self) -> None:
        self.port = serial.Serial('/dev/ttyUSB0', 57600)
        self.address = 0xFFFFFFFF

    def send_payload(self, instruction, payload: list=[]):
        data = [0xEF, 0x01]
        data.extend(self.address.to_bytes(4, 'big'))

        identifier = 0x01
        checksum = instruction + identifier

        data.extend([identifier])

        length = len(payload) + 3
        length = length.to_bytes(2, 'big')
        data.extend(length)
        data.extend([instruction])
        data.extend(payload)

        checksum += length[0]
        checksum += length[1]

        for byte in payload:
            checksum += byte

        data.extend(checksum.to_bytes(2, 'big'))

        self.port.write(data)

    def set_color(self):
        self.send_payload(0x35, [0x03, 0x00, 0x08, 0x00])

    def auto_enroll(self):
        self.send_payload(0x31, [0xFF, 0x00, 0x00, 0x00, 0x01])

    def auto_identify(self):
        self.send_payload(0x32, [0x03, 0x00, 199, 0x00, 0x00])


def main():
    controller = Controller()
    while True:
        input()
        controller.auto_identify()

if __name__ == '__main__':
    main()