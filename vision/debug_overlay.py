def _color(r, g, b):
    try:
        from maix import image
        return image.Color.from_rgb(r, g, b)
    except Exception:
        return (r, g, b)


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


def _image_dim(img, name, default):
    value = getattr(img, name, None)
    if callable(value):
        try:
            return int(value())
        except Exception:
            return int(default)
    if value is not None:
        try:
            return int(value)
        except Exception:
            pass
    return int(default)


def draw_overlay(img, result, setpoint_x, setpoint_y, seq=0, fps=0, message=""):
    text = "FPS:%d" % int(fps)
    width = _image_dim(img, "width", 160)
    height = _image_dim(img, "height", 120)
    x = max(0, width - 58)
    y = max(0, height - 18)
    _safe_call(img, "draw_string", x, y, text, COLOR_WHITE)
    return img
