import os, sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import camera_config, calibration_config, detector_config
from maix_platform.maix_camera import CameraSource
from maix_platform.maix_display import DisplayAdapter
from maix_platform.timebase import sleep_ms
from vision.black_border_detector import BlackBorderDetector
from vision.debug_overlay import draw_overlay


def main():
    if calibration_config.USE_IMAGE_CENTER:
        sx = camera_config.CAMERA_WIDTH // 2 + calibration_config.OFFSET_X
        sy = camera_config.CAMERA_HEIGHT // 2 + calibration_config.OFFSET_Y
    else:
        sx = int(calibration_config.SETPOINT_X) + calibration_config.OFFSET_X
        sy = int(calibration_config.SETPOINT_Y) + calibration_config.OFFSET_Y
    cam = CameraSource()
    disp = DisplayAdapter(enabled=True)
    cam.open()
    disp.open()
    detector = BlackBorderDetector(camera_config.CAMERA_WIDTH, camera_config.CAMERA_HEIGHT, sx, sy)
    print("detector test started. Aim MaixCAM2 at the black-border target.")
    print("logic=lasttestfirst.py resolution=%dx%d" % (camera_config.CAMERA_WIDTH, camera_config.CAMERA_HEIGHT))

    seq = 0
    last_time = time.time()
    fps = 0
    while seq < 500:
        seq += 1
        img = cam.read()

        current_time = time.time()
        dt = current_time - last_time
        if dt > 0:
            fps = 1.0 / dt
        last_time = current_time

        result = detector.detect(img)
        display_img = getattr(result, "display_img", img)
        draw_overlay(
            display_img,
            result,
            sx,
            sy,
            seq=seq,
            fps=fps,
            message="%s %s" % (result.method, result.note),
        )
        disp.show(display_img)
        print_every = max(1, int(detector_config.DIAGNOSTIC_PRINT_EVERY_N_FRAMES))
        if seq % print_every == 0:
            print(result)
        sleep_ms(1)
    print("detector test finished")


if __name__ == "__main__":
    main()

