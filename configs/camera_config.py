# MaixCAM2 camera configuration.
# 160x120 matches the low-compute detector path and leaves headroom for later work.

CAMERA_WIDTH = 160
CAMERA_HEIGHT = 120

# Keep RGB because the lightweight detector converts the camera frame through
# image.image2cv(...) and then grayscale/adaptive-thresholds it.
CAMERA_FORMAT = "rgb"  # "rgb" or "grayscale"

# Image orientation correction.
FLIP_X = False
FLIP_Y = False
ROTATE_DEG = 0

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
