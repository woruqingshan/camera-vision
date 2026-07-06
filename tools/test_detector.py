import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import camera_config, calibration_config
from maix_platform.maix_camera import CameraSource
from maix_platform.maix_display import DisplayAdapter
from maix_platform.timebase import sleep_ms
from vision.black_border_detector import BlackBorderDetector
from vision.debug_overlay import draw_overlay


def main():
    sx = camera_config.CAMERA_WIDTH // 2 if calibration_config.USE_IMAGE_CENTER else calibration_config.SETPOINT_X
    sy = camera_config.CAMERA_HEIGHT // 2 if calibration_config.USE_IMAGE_CENTER else calibration_config.SETPOINT_Y
    cam = CameraSource()
    disp = DisplayAdapter(enabled=True)
    cam.open()
    disp.open()
    detector = BlackBorderDetector(camera_config.CAMERA_WIDTH, camera_config.CAMERA_HEIGHT, sx, sy)
    print("detector test started. Aim MaixCAM2 at the black-border target.")
    seq = 0
    while seq < 500:
        seq += 1
        img = cam.read()
        result = detector.detect(img)
        draw_overlay(img, result, sx, sy, seq=seq, fps=0)
        disp.show(img)
        if seq % 10 == 0:
            print(result)
        sleep_ms(1)
    print("detector test finished")


if __name__ == "__main__":
    main()
