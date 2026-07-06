def _color(r, g, b):
    try:
        from maix import image
        return image.Color.from_rgb(r, g, b)
    except Exception:
        return (r, g, b)


COLOR_GREEN = _color(0, 255, 0)
COLOR_RED = _color(255, 0, 0)
COLOR_YELLOW = _color(255, 255, 0)
COLOR_BLUE = _color(0, 128, 255)
COLOR_WHITE = _color(255, 255, 255)


def _safe_call(obj, method, *args, **kwargs):
    fn = getattr(obj, method, None)
    if not callable(fn):
        return False
    try:
        fn(*args, **kwargs)
        return True
    except TypeError:
        try:
            fn(*args)
            return True
        except Exception:
            return False
    except Exception:
        return False


def draw_cross(img, x, y, color, size=8):
    if _safe_call(img, "draw_cross", int(x), int(y), color=color, size=size):
        return
    # Fallback: two lines if available.
    _safe_call(img, "draw_line", int(x - size), int(y), int(x + size), int(y), color=color)
    _safe_call(img, "draw_line", int(x), int(y - size), int(x), int(y + size), color=color)


def draw_overlay(img, result, setpoint_x, setpoint_y, seq=0, fps=0, message=""):
    draw_cross(img, setpoint_x, setpoint_y, COLOR_BLUE, size=10)
    if result and result.found:
        if result.bbox:
            x, y, w, h = result.bbox
            _safe_call(img, "draw_rect", int(x), int(y), int(w), int(h), color=COLOR_GREEN, thickness=2)
        draw_cross(img, result.cx, result.cy, COLOR_RED, size=8)
        text = "T seq=%d dx=%d dy=%d c=%d fps=%d" % (
            seq, result.dx, result.dy, result.confidence, int(fps))
    else:
        text = "LOST seq=%d fps=%d" % (seq, int(fps))
    if message:
        text = text + " " + str(message)[:40]
    _safe_call(img, "draw_string", 4, 4, text, color=COLOR_YELLOW)
    return img
