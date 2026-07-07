# Black-border target detector configuration.
# MaixPy find_blobs uses LAB thresholds: (L_min, L_max, A_min, A_max, B_min, B_max).
# For a black border, keep L low and allow broad A/B ranges.

BLACK_LAB_THRESHOLD = (0, 55, -128, 127, -128, 127)

# Minimum and maximum detected bounding-box area as a fraction of the image area.
# Tune these after looking at actual MaixCAM2 overlay images.
MIN_AREA_RATIO = 0.01
MAX_AREA_RATIO = 0.80

# A4 aspect ratio is approximately 1.414. Use max(w, h) / min(w, h) so portrait
# and landscape are both accepted. This also tolerates perspective distortion.
MIN_ASPECT = 1.05
MAX_ASPECT = 2.20
PREFERRED_ASPECT = 1.414

# Candidate quality filters.
MIN_CONFIDENCE = 35  # 0~100
MIN_PIXELS_THRESHOLD = 80
MIN_AREA_THRESHOLD = 80
MERGE_BLOBS = True

# Target continuity filter: if a new center jumps too far, reduce confidence.
MAX_CENTER_JUMP_PX = 90

# Optional region of interest. None means use whole image.
# Format: (x, y, w, h)
ROI = None

# If Maix native find_blobs fails, optional OpenCV fallback may be tried.
# This fallback is best-effort only; Maix native APIs remain the primary path.
ENABLE_OPENCV_FALLBACK = True
OPENCV_BLACK_THRESHOLD = 70

# Diagnostics used by test_detector. Candidate summaries are capped to keep
# terminal output readable and avoid excessive work on the board.
DIAGNOSTIC_MAX_CANDIDATES = 4
DIAGNOSTIC_PRINT_EVERY_N_FRAMES = 10
