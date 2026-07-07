# Black-border target detector configuration.
# The current production detector uses a low-cost OpenCV contour pipeline derived
# from lasttestfirst.py, while main.py keeps the TI @T/@D protocol unchanged.

# Legacy Maix find_blobs parameters retained for old tools/tests.
BLACK_LAB_THRESHOLD = (0, 55, -128, 127, -128, 127)
MIN_PIXELS_THRESHOLD = 80
MIN_AREA_THRESHOLD = 80
MERGE_BLOBS = True
ROI = None
ENABLE_OPENCV_FALLBACK = False
OPENCV_BLACK_THRESHOLD = 70

# Shared confidence settings.
MIN_CONFIDENCE = 35
MIN_AREA_RATIO = 0.01
MAX_AREA_RATIO = 0.80
MIN_ASPECT = 1.05
MAX_ASPECT = 2.20
PREFERRED_ASPECT = 1.414
MAX_CENTER_JUMP_PX = 90

# Lightweight contour detector settings.
CV_AREA_MIN = 50
CV_AREA_MAX_RATIO = 0.62
CV_BORDER_MARGIN = 2
CV_EPSILON_RATIO = 0.045
CV_ASPECT_MIN = 1.0
CV_ASPECT_MAX = 3.4
CV_CENTER_PAIR_TOLERANCE = 9
CV_TRACK_RADIUS = 38
CV_SMOOTH_ALPHA = 0.35
CV_MAX_LOST_KEEP = 8
CV_MAX_CONTOURS = 12
CV_CLOSE_KERNEL = (3, 3)
CV_ADAPTIVE_BLOCK_SIZE = 11
CV_ADAPTIVE_C = 2
CV_INNER_BONUS = 8

# Diagnostics used by test_detector. Candidate summaries are capped to keep
# terminal output readable and avoid excessive work on the board.
DIAGNOSTIC_MAX_CANDIDATES = 4
DIAGNOSTIC_PRINT_EVERY_N_FRAMES = 10
