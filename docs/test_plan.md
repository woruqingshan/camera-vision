# Test Plan

## Stage 1: Local board smoke test

- Run display test.
- Run camera test.
- Confirm image orientation.

## Stage 2: UART output test

- Connect MaixCAM2 TX to USB-TTL RX.
- Confirm ASCII `@T` frames at 115200.

## Stage 3: Detector test

- Run `tools/test_detector.py`.
- Tune threshold and area filters.

## Stage 4: TI Bridge parser test

- Connect MaixCAM2 TX to TI Bridge RX.
- Keep F32C disconnected or in dry-run.
- Confirm TI Bridge parses frames.

## Stage 5: Static aim

- Connect F32C.
- Use conservative speed limits on TI Bridge.
- Adjust yaw/pitch direction on TI Bridge if cloud platform moves away from target.

## Stage 6: Dynamic tracking

- Run low-speed chassis line tracking.
- Verify target loss/reacquisition behavior.
