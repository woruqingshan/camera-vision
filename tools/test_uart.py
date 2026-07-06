import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import serial_config
from maix_platform.maix_uart import UartSender
from maix_platform.timebase import sleep_ms
from protocol.ti_bridge_protocol import build_target_message


def main():
    sender = UartSender()
    sender.open()
    print("sending target test frames. include_seq=", serial_config.INCLUDE_SEQUENCE)
    seq = 0
    while seq < 80:
        seq += 1
        if seq < 40:
            dx = 30 - seq
            dy = -10
            msg = build_target_message(seq, True, dx, dy, 90, serial_config.INCLUDE_SEQUENCE)
        elif seq < 60:
            msg = build_target_message(seq, False, 0, 0, 0, serial_config.INCLUDE_SEQUENCE)
        else:
            dx = seq - 60
            dy = 5
            msg = build_target_message(seq, True, dx, dy, 85, serial_config.INCLUDE_SEQUENCE)
        sender.write_line(msg)
        print(msg, end="")
        sleep_ms(40)
    sender.write_line(build_target_message(seq, False, 0, 0, 0, serial_config.INCLUDE_SEQUENCE))


if __name__ == "__main__":
    main()
