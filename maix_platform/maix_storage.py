from configs import camera_config as cfg


def ensure_dir(path):
    try:
        import os
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as exc:
        print("[storage] mkdir failed:", exc)
        return False


def save_frame_if_enabled(img, seq, reason="frame"):
    if not cfg.SAVE_DEBUG_FRAMES:
        return False
    if not ensure_dir(cfg.SAVE_DIR):
        return False
    path = "%s/%06d_%s.jpg" % (cfg.SAVE_DIR.rstrip("/"), int(seq), reason)
    try:
        img.save(path)
        print("[storage] saved", path)
        return True
    except Exception as exc:
        print("[storage] save failed:", exc)
        return False
