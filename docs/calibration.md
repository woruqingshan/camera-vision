# Calibration

First MVP uses image center as setpoint.

After mechanical installation, calibrate laser setpoint:

1. Fix car and target.
2. Make the laser physically hit the target center.
3. Run `python tools/calibrate_setpoint.py`.
4. Read stable `CALIB_CANDIDATE cx=... cy=...` output.
5. Put values into `configs/calibration_config.py`:

```python
USE_IMAGE_CENTER = False
SETPOINT_X = <cx>
SETPOINT_Y = <cy>
```

Do not assume image center equals laser hit point.
