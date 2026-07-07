import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.ti_bridge_protocol import (
    build_target_message,
    build_target_packet,
    parse_target_message,
    parse_target_packet,
)


def hex_line(data):
    return " ".join("%02X" % value for value in data)


def main():
    ascii_samples = [
        build_target_message(1, True, 12, -8, 92, include_seq=True),
        build_target_message(2, False, 0, 0, 0, include_seq=True),
        build_target_message(0, True, 12, -8, 92, include_seq=False),
    ]
    for msg in ascii_samples:
        print(msg, end="")
        print(parse_target_message(msg))

    binary_samples = [
        build_target_packet(1, True, 92, 58, 12, -8, 92, fps=60),
        build_target_packet(2, False, 0, 0, 0, 0, 0, fps=60),
    ]
    for packet in binary_samples:
        print(hex_line(packet))
        print(parse_target_packet(packet))


if __name__ == "__main__":
    main()
