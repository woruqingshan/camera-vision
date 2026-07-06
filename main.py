"""Single entry point for MaixCAM2.

Upload the whole camera_vision_firmware_maixcam2 folder to MaixCAM2 and run:
    python main.py

Select runtime behavior by editing configs/app_config.py::RUN_MODE.
This avoids needing to run files inside tools/ directly on the board.
"""

import os
import sys

# Make imports stable when MaixVision runs this file from a different working directory.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from configs import app_config, camera_config, calibration_config, serial_config
from maix_platform.timebase import ticks_ms, sleep_ms
from maix_platform.maix_camera import CameraSource
from maix_platform.maix_display import DisplayAdapter
from maix_platform.maix_uart import UartSender
from maix_platform.maix_storage import save_frame_if_enabled
from protocol.ti_bridge_protocol import build_target_message, build_debug_message
from vision.black_border_detector import BlackBorderDetector
from vision.debug_overlay import draw_overlay


def _need_exit():
    try:
        from maix import app
        return app.need_exit()
    except Exception:
        return False


def _get_setpoint():
    if calibration_config.USE_IMAGE_CENTER:
        return (
            camera_config.CAMERA_WIDTH // 2 + calibration_config.OFFSET_X,
            camera_config.CAMERA_HEIGHT // 2 + calibration_config.OFFSET_Y,
        )
    return (
        int(calibration_config.SETPOINT_X) + calibration_config.OFFSET_X,
        int(calibration_config.SETPOINT_Y) + calibration_config.OFFSET_Y,
    )


def run_vision_main():
    """Competition/MVP vision loop.

    Capture image -> detect target -> draw overlay -> send @T frame to TI Bridge.
    """
    print("[%s] version=%s mode=vision" % (app_config.APP_NAME, app_config.VERSION))
    setpoint_x, setpoint_y = _get_setpoint()
    print(
        "camera=%dx%d setpoint=(%d,%d) uart=%s baud=%d" % (
            camera_config.CAMERA_WIDTH,
            camera_config.CAMERA_HEIGHT,
            setpoint_x,
            setpoint_y,
            serial_config.UART_DEVICE,
            serial_config.UART_BAUDRATE,
        )
    )

    cam = CameraSource()
    disp = DisplayAdapter(enabled=camera_config.DEBUG_DISPLAY)
    uart = UartSender()

    cam.open()
    disp.open()
    uart.open()

    detector = BlackBorderDetector(
        camera_config.CAMERA_WIDTH,
        camera_config.CAMERA_HEIGHT,
        setpoint_x,
        setpoint_y,
    )

    seq = 0
    last_send_ms = 0
    last_fps_ms = ticks_ms()
    fps = 0
    fps_count = 0
    lost_prev = True
    send_period_ms = int(1000 / max(1, serial_config.TARGET_SEND_HZ))

    try:
        while not _need_exit():
            if app_config.MAX_RUN_FRAMES and seq >= app_config.MAX_RUN_FRAMES:
                break

            seq = (seq + 1) & 0xFFFF
            img = cam.read()
            result = detector.detect(img)

            now = ticks_ms()
            fps_count += 1
            if now - last_fps_ms >= 1000:
                fps = fps_count
                fps_count = 0
                last_fps_ms = now

            if camera_config.DRAW_OVERLAY:
                draw_overlay(img, result, setpoint_x, setpoint_y, seq=seq, fps=fps)
            if camera_config.DEBUG_DISPLAY and seq % max(1, camera_config.DISPLAY_EVERY_N_FRAMES) == 0:
                disp.show(img)

            if camera_config.SAVE_DEBUG_FRAMES:
                if seq % max(1, camera_config.SAVE_FRAME_EVERY_N) == 0:
                    save_frame_if_enabled(img, seq, "periodic")
                if camera_config.SAVE_ON_LOST and (not result.found) and not lost_prev:
                    save_frame_if_enabled(img, seq, "lost")
                if camera_config.SAVE_ON_REACQUIRED and result.found and lost_prev:
                    save_frame_if_enabled(img, seq, "reacquired")

            if now - last_send_ms >= send_period_ms:
                msg = build_target_message(
                    seq,
                    result.found,
                    result.dx,
                    result.dy,
                    result.confidence,
                    serial_config.INCLUDE_SEQUENCE,
                )
                uart.write_line(msg)
                if serial_config.SEND_DEBUG_FRAME and result.found:
                    uart.write_line(
                        build_debug_message(
                            seq,
                            result.cx,
                            result.cy,
                            result.dx,
                            result.dy,
                            result.confidence,
                            fps,
                        )
                    )
                last_send_ms = now

            if app_config.PRINT_EVERY_N_FRAMES and seq % app_config.PRINT_EVERY_N_FRAMES == 0:
                print(
                    "seq=%d found=%s dx=%d dy=%d conf=%d fps=%d note=%s" % (
                        seq,
                        result.found,
                        result.dx,
                        result.dy,
                        result.confidence,
                        fps,
                        result.note,
                    )
                )

            lost_prev = not result.found
            sleep_ms(1)
    except KeyboardInterrupt:
        print("stopped by keyboard")
    finally:
        try:
            uart.write_line(build_target_message(seq, False, 0, 0, 0, serial_config.INCLUDE_SEQUENCE))
        except Exception:
            pass
        try:
            uart.close()
        except Exception:
            pass
        try:
            cam.close()
        except Exception:
            pass
        print("vision loop exit")


def run_selected_mode(mode):
    """Dispatch debug/production modes from a single main.py entry."""
    mode = (mode or "vision").strip().lower()
    aliases = {
        "main": "vision",
        "run": "vision",
        "competition": "vision",
        "camera": "test_camera",
        "display": "test_display",
        "uart": "test_uart",
        "detector": "test_detector",
        "protocol": "test_protocol",
        "calibration": "calibrate_setpoint",
        "calibrate": "calibrate_setpoint",
    }
    mode = aliases.get(mode, mode)

    print("main.py dispatch RUN_MODE=%s" % mode)

    if mode == "vision":
        return run_vision_main()
    if mode == "test_display":
        from tools.test_display import main as tool_main
        return tool_main()
    if mode == "test_camera":
        from tools.test_camera import main as tool_main
        return tool_main()
    if mode == "test_uart":
        from tools.test_uart import main as tool_main
        return tool_main()
    if mode == "test_protocol":
        from tools.test_protocol_output import main as tool_main
        return tool_main()
    if mode == "test_detector":
        from tools.test_detector import main as tool_main
        return tool_main()
    if mode == "calibrate_setpoint":
        from tools.calibrate_setpoint import main as tool_main
        return tool_main()

    print("ERROR: unknown RUN_MODE=%s" % mode)
    print("Valid modes: vision, test_display, test_camera, test_uart, test_protocol, test_detector, calibrate_setpoint")


def main():
    return run_selected_mode(app_config.RUN_MODE)


if __name__ == "__main__":
    main()
