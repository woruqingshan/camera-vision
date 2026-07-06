import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import camera_config
from maix_platform.maix_camera import CameraSource
from maix_platform.maix_display import DisplayAdapter
from maix_platform.timebase import sleep_ms


def main():
    cam = CameraSource()
    disp = DisplayAdapter(enabled=True)
    cam.open()
    disp.open()
    frame = 0
    print("camera test started, resolution=%dx%d" % (camera_config.CAMERA_WIDTH, camera_config.CAMERA_HEIGHT))
    while frame < 200:
        frame += 1
        img = cam.read()
        disp.show(img)
        if frame % 20 == 0:
            print("frame", frame, img)
        sleep_ms(1)
    print("camera test finished")


if __name__ == "__main__":
    main()
