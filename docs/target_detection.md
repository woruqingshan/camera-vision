# Target Detection

MVP algorithm:

1. Read RGB image from MaixCAM2.
2. Use LAB threshold to find black blobs.
3. Filter candidates by area ratio and A4-like aspect ratio.
4. Select highest-confidence candidate.
5. Use bounding-box center as target center.
6. Compute `dx = cx - setpoint_x`, `dy = cy - setpoint_y`.

The target is expected to be an A4 sheet with a clear black border. If the detector sees black track lines or black support structure, tune ROI and area filters.

Future upgrades:

- Homography-based center projection from A4 plane.
- Red-ring validation.
- ROI based on expected target position.
- Temporal tracking and confidence smoothing.
