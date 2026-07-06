import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import camera_config
from maix_platform.maix_camera import CameraSource
from maix_platform.maix_display import DisplayAdapter
from maix_platform.timebase import sleep_ms
from vision.black_border_detector import BlackBorderDetector
from vision.debug_overlay import draw_overlay


def main():
    # Use image center as temporary setpoint, but print the detected target center.
    # Manual calibration procedure:
    # 1. Adjust cloud platform/laser so laser hits target center.
    # 2. Read printed cx, cy.
    # 3. Write those values into configs/calibration_config.py as SETPOINT_X/Y,
    #    then set USE_IMAGE_CENTER = False.
    sx = camera_config.CAMERA_WIDTH // 2
    sy = camera_config.CAMERA_HEIGHT // 2
    cam = CameraSource()
    disp = DisplayAdapter(enabled=True)
    cam.open()
    disp.open()
    detector = BlackBorderDetector(camera_config.CAMERA_WIDTH, camera_config.CAMERA_HEIGHT, sx, sy)
    print("calibration helper started")
    print("When laser hits target center, record printed cx/cy as SETPOINT_X/Y.")
    seq = 0
    while seq < 1000:
        seq += 1
        img = cam.read()
        result = detector.detect(img)
        draw_overlay(img, result, sx, sy, seq=seq, fps=0)
        disp.show(img)
        if result.found and seq % 10 == 0:
            print("CALIB_CANDIDATE cx=%d cy=%d conf=%d" % (result.cx, result.cy, result.confidence))
        sleep_ms(1)


if __name__ == "__main__":
    main()
