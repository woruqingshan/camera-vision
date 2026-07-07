def clamp_int(value, low, high):
    value = int(value)
    if value < low:
        return low
    if value > high:
        return high
    return value


FRAME_HEAD_0 = 0xA5
FRAME_HEAD_1 = 0x5A
FRAME_TAIL_0 = 0x0D
FRAME_TAIL_1 = 0x0A
FRAME_TYPE_TARGET = 0x01
TARGET_PACKET_SIZE = 19


def _u16_le(value):
    value = int(value) & 0xFFFF
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def _i16_le(value):
    value = clamp_int(value, -32768, 32767) & 0xFFFF
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def _read_i16_le(data, index):
    value = int(data[index]) | (int(data[index + 1]) << 8)
    if value & 0x8000:
        value -= 0x10000
    return value


def xor_bcc(data):
    bcc = 0
    for value in data:
        bcc ^= int(value) & 0xFF
    return bcc & 0xFF


def build_target_packet(seq, found, cx, cy, dx, dy, confidence, fps=0):
    """Build fixed-length binary MaixCAM2 -> TI target packet.

    Packet layout, 19 bytes total:
        A5 5A
        type:u8                 fixed 0x01
        seq:u16le
        flags:u8                bit0 found, bit1 stable(confidence >= 60)
        cx:i16le cy:i16le
        dx:i16le dy:i16le       pixel error in current camera resolution
        confidence:u8
        fps:u8
        bcc:u8                  XOR from type through fps
        0D 0A
    """
    seq = int(seq) & 0xFFFF
    found = bool(found)
    confidence = clamp_int(confidence, 0, 100)
    fps = clamp_int(fps, 0, 255)
    if not found:
        cx = 0
        cy = 0
        dx = 0
        dy = 0
        confidence = 0

    flags = 0x01 if found else 0x00
    if found and confidence >= 60:
        flags |= 0x02

    payload = (
        bytes((FRAME_TYPE_TARGET,))
        + _u16_le(seq)
        + bytes((flags,))
        + _i16_le(cx)
        + _i16_le(cy)
        + _i16_le(dx)
        + _i16_le(dy)
        + bytes((confidence, fps))
    )
    return (
        bytes((FRAME_HEAD_0, FRAME_HEAD_1))
        + payload
        + bytes((xor_bcc(payload), FRAME_TAIL_0, FRAME_TAIL_1))
    )


def parse_target_packet(packet):
    """PC-side/self-test parser for binary_v1 packets."""
    data = bytes(packet)
    if len(data) != TARGET_PACKET_SIZE:
        raise ValueError("invalid target packet size")
    if data[0] != FRAME_HEAD_0 or data[1] != FRAME_HEAD_1:
        raise ValueError("invalid target packet header")
    if data[17] != FRAME_TAIL_0 or data[18] != FRAME_TAIL_1:
        raise ValueError("invalid target packet tail")
    payload = data[2:16]
    if xor_bcc(payload) != data[16]:
        raise ValueError("invalid target packet checksum")
    if data[2] != FRAME_TYPE_TARGET:
        raise ValueError("invalid target packet type")

    seq = int(data[3]) | (int(data[4]) << 8)
    flags = int(data[5])
    return {
        "type": int(data[2]),
        "seq": seq,
        "found": 1 if (flags & 0x01) else 0,
        "stable": 1 if (flags & 0x02) else 0,
        "flags": flags,
        "cx": _read_i16_le(data, 6),
        "cy": _read_i16_le(data, 8),
        "dx": _read_i16_le(data, 10),
        "dy": _read_i16_le(data, 12),
        "confidence": int(data[14]),
        "fps": int(data[15]),
    }


def build_target_message(seq, found, dx, dy, confidence, include_seq=True):
    """Build ASCII MaixCAM2 -> TI Bridge target message.

    V2 default:
        @T,seq,found,dx,dy,confidence\n
    Legacy:
        @T,found,dx,dy,confidence\n
    Values are clamped to keep the receiver parser simple and safe.
    """
    seq = int(seq) & 0xFFFF
    found = 1 if found else 0
    dx = clamp_int(dx, -9999, 9999)
    dy = clamp_int(dy, -9999, 9999)
    confidence = clamp_int(confidence, 0, 100)
    if not found:
        dx = 0
        dy = 0
        confidence = 0
    if include_seq:
        return "@T,%d,%d,%d,%d,%d\n" % (seq, found, dx, dy, confidence)
    return "@T,%d,%d,%d,%d\n" % (found, dx, dy, confidence)


def build_debug_message(seq, cx, cy, dx, dy, confidence, fps):
    return "@D,%d,%d,%d,%d,%d,%d,%d\n" % (
        int(seq) & 0xFFFF, int(cx), int(cy), int(dx), int(dy),
        clamp_int(confidence, 0, 100), int(fps))


def parse_target_message(line):
    """Small parser for PC-side/self-test use. TI Bridge has its own C parser."""
    text = line.decode() if isinstance(line, bytes) else str(line)
    text = text.strip()
    if not text.startswith("@T,"):
        raise ValueError("not a target message")
    parts = text.split(",")
    if len(parts) == 6:
        return {
            "seq": int(parts[1]),
            "found": int(parts[2]),
            "dx": int(parts[3]),
            "dy": int(parts[4]),
            "confidence": int(parts[5]),
        }
    if len(parts) == 5:
        return {
            "seq": None,
            "found": int(parts[1]),
            "dx": int(parts[2]),
            "dy": int(parts[3]),
            "confidence": int(parts[4]),
        }
    raise ValueError("invalid target message field count")
