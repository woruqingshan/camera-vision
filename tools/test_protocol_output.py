import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.ti_bridge_protocol import build_target_message, parse_target_message


def main():
    samples = [
        build_target_message(1, True, 12, -8, 92, include_seq=True),
        build_target_message(2, False, 0, 0, 0, include_seq=True),
        build_target_message(0, True, 12, -8, 92, include_seq=False),
    ]
    for msg in samples:
        print(msg, end="")
        print(parse_target_message(msg))


if __name__ == "__main__":
    main()
