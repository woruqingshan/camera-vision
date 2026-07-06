# Further Development Plan

## P0 - Bring-up

1. Run official MaixCAM2 camera + display examples.
2. Run this project's display and camera tests.
3. Confirm UART output to PC.
4. Confirm TI Bridge parser compatibility.

## P1 - MVP visual tracking

1. Tune black LAB threshold for your printed target.
2. Tune area/aspect filters.
3. Confirm stable `dx/dy` at static target positions.
4. Run static closed-loop aim through TI Bridge.

## P2 - Calibration

1. Add calibrated laser setpoint.
2. Record calibration photos.
3. Confirm `dx/dy` tends to zero when laser hits target center.

## P3 - Robustness

1. Add ROI to avoid black supports or track lines.
2. Add temporal smoothing on MaixCAM2 if needed.
3. Add confidence drop when target jumps too far.
4. Save debug frames on lost/reacquired events.

## P4 - Accuracy upgrade

1. Use quadrilateral corners instead of bbox when Maix API provides them reliably.
2. Add Homography A4-center estimation.
3. Use red-ring validation as a secondary check.

## P5 - Competition mode

1. Disable high-frequency prints.
2. Disable image saving.
3. Optionally reduce display frequency.
4. Fix all cable strain relief and power/GND reliability.
