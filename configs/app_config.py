# Application-level runtime configuration.

APP_NAME = "camera_vision_firmware_maixcam2"
VERSION = "0.1.0-mvp"

# Runtime mode selected by main.py. Upload the folder and run only main.py on MaixCAM2.
# Valid values: vision, test_display, test_camera, test_uart, test_protocol, test_detector, calibrate_setpoint.
RUN_MODE = "test_detector"

# Main loop control.
MAX_RUN_FRAMES = 0  # 0 means run forever
PRINT_EVERY_N_FRAMES = 15

# Lost target behavior: always send @T lost frames instead of stopping UART output.
SEND_LOST_FRAME_CONTINUOUSLY = True
