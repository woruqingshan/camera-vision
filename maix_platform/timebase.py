def ticks_ms():
    try:
        from maix import time
        return int(time.ticks_ms())
    except Exception:
        try:
            import time as pytime
            return int(pytime.time() * 1000)
        except Exception:
            return 0


def sleep_ms(ms):
    try:
        from maix import time
        time.sleep_ms(int(ms))
    except Exception:
        import time as pytime
        pytime.sleep(float(ms) / 1000.0)
