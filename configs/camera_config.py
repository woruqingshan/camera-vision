# MaixCAM2 camera configuration for the first MVP.
# Start with QVGA for lower latency. If the target is too small, switch to 640x480.

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# MaixPy camera format. Keep as "rgb" for the first version because Maix image APIs
# such as find_blobs use LAB thresholds derived from RGB images.
CAMERA_FORMAT = "rgb"  # "rgb" or "grayscale"

# Image orientation correction. These are applied only if supported by the current
# MaixPy Image API. If unsupported, README explains how to adjust after testing.
FLIP_X = False
FLIP_Y = False
ROTATE_DEG = 0  # 0, 90, 180, 270; not all APIs support all rotations

# Display and debug settings.
DEBUG_DISPLAY = True
DISPLAY_EVERY_N_FRAMES = 1
DRAW_OVERLAY = True

# Optional image saving. Keep disabled in competition mode to avoid I/O stalls.
SAVE_DEBUG_FRAMES = False
SAVE_FRAME_EVERY_N = 60
SAVE_ON_LOST = True
SAVE_ON_REACQUIRED = True
SAVE_DIR = "/root/target_debug_frames"
