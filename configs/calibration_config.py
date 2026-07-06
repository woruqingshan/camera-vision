# Initial setpoint configuration.
# First MVP uses image center. After laser-camera calibration, set USE_IMAGE_CENTER = False
# and fill SETPOINT_X / SETPOINT_Y with the calibrated laser-hit pixel.

USE_IMAGE_CENTER = True
SETPOINT_X = 160
SETPOINT_Y = 120

# Optional manual offsets applied after center calculation.
OFFSET_X = 0
OFFSET_Y = 0
