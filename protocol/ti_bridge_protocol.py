def clamp_int(value, low, high):
    value = int(value)
    if value < low:
        return low
    if value > high:
        return high
    return value


def build_target_message(seq, found, dx, dy, confidence, include_seq=True):
    """Build MaixCAM2 -> TI Bridge target message.

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
