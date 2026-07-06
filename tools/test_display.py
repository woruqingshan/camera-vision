import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maix_platform.maix_display import DisplayAdapter
from maix_platform.timebase import sleep_ms


def main():
    try:
        from maix import image
    except Exception as exc:
        print("maix.image unavailable:", exc)
        return
    disp = DisplayAdapter(enabled=True)
    disp.open()
    img = image.Image(320, 240)
    try:
        img.draw_rect(0, 0, 320, 240, color=image.Color.from_rgb(0, 0, 0), thickness=-1)
        img.draw_string(20, 20, "MaixCAM2 display OK", color=image.Color.from_rgb(255, 255, 0))
        img.draw_cross(160, 120, color=image.Color.from_rgb(255, 0, 0), size=15)
    except Exception as exc:
        print("draw warning:", exc)
    for _ in range(100):
        disp.show(img)
        sleep_ms(20)


if __name__ == "__main__":
    main()
