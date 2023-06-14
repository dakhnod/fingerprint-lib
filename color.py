#!/usr/bin/env python

import serial
import time
import requests
import argparse

class Controller():
    def __init__(self) -> None:
        self.port = serial.Serial('/dev/ttyUSB0', 115200)
        self.address = 0xFFFFFFFF

    def serial_read(self, timeout=10, timeout_per_char=0.1):
        data = bytearray()
        self.port.timeout = timeout
        # read first char
        data.extend(self.port.read())
        self.port.timeout = timeout_per_char
        while True:
            chunk = self.port.read()
            if len(chunk) == 0:
                return data
            data.extend(chunk)

    def response_read(self):
        response = self.serial_read()
        if len(response) == 0:
            return None
        response = list(response)
        if response[0:2] != [0xEF, 0x01]:
            raise RuntimeError('Wrong start bytes')
        if response[6] != 0x07:
            raise RuntimeError('Wrong reponse package identifier')
        length = int.from_bytes(response[7:9])
        return response[9:9+length]

    def send_payload(self, identifier, instruction, payload: list=[]):
        data = [0xEF, 0x01]
        data.extend(self.address.to_bytes(4, 'big'))

        checksum = instruction + identifier

        data.extend([identifier])

        length = len(payload) + 3
        length = length.to_bytes(2)
        data.extend(length)
        data.extend([instruction])
        data.extend(payload)

        checksum += length[0]
        checksum += length[1]

        for byte in payload:
            checksum += byte

        data.extend(checksum.to_bytes(2))

        self.port.write(data)

    def send_command(self, instruction, payload):
        return self.send_payload(0x01, instruction, payload)

    def set_color(self):
        self.send_command(0x35, [0x03, 0x00, 0x08, 0x00])

    def auto_enroll(self):
        self.send_command(0x31, [0xFF, 0x00, 0x00, 0x00, 0x01])

    def set_sys_param(self, parameter, value):
        self.send_command(0x0e, [parameter, value])
        print(self.response_read())

    def auto_identify(self):
        self.send_command(0x32, [0x03, 0x00, 199, 0x00, 0x00])
        while True:
            response = self.response_read()
            if response is None:
                return
            status_code = response[0]
            status = {
                0x00: 'success',
                0x01: 'fail',
                0x09: 'not found',
                0x0b: 'id out of range',
                0x22: 'finger template is empty',
                0x24: 'finger library is empty',
                0x26: 'timeout'
            }[status_code]
            step = response[1]
            position = int.from_bytes(response[2:4])
            score = int.from_bytes(response[4:6])
            print(f'status: {status}, step: {step}, position: {position}, score: {score}')
            if status_code == 0x00:
                yield position, score
                return
            elif status_code == 0x09:
                yield None
            elif status_code != 0x09:
                print('identification done')
                return

def main():
    controller = Controller()
    # controller.set_sys_param(0x04, 12)
    # return

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--enroll', required=False, action='store_true')

    args = parser.parse_args()

    if args.enroll:
        controller.auto_enroll()
        return

    while True:
        print('identifying')
        for id in controller.auto_identify():
            if id is not None:
                id, score = id
                id = ids[id]
                send_finger(**id, score=score)
            else:
                send_finger('unknown', '', '', 0)
            time.sleep(0.5)

if __name__ == '__main__':
    main()
