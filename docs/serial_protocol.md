# Serial Protocol

MaixCAM2 sends target observations to the TI board. The F32C gimbal still uses
its own WHEELTEC motor protocol on the TI-to-gimbal UART.

## Recommended: binary_v1

`configs/serial_config.py` defaults to `PROTOCOL_MODE = "binary_v1"`.

Each target packet is fixed at 19 bytes:

```text
A5 5A 01 seq_lo seq_hi flags cx_lo cx_hi cy_lo cy_hi dx_lo dx_hi dy_lo dy_hi confidence fps bcc 0D 0A
```

Fields:

| Byte | Field | Type | Meaning |
| --- | --- | --- | --- |
| 0..1 | header | u8 | `A5 5A` |
| 2 | type | u8 | `01` target frame |
| 3..4 | seq | u16 little-endian | frame counter, wraps at 65535 |
| 5 | flags | u8 | bit0 found, bit1 stable (`confidence >= 60`) |
| 6..7 | cx | i16 little-endian | detected center x, pixels |
| 8..9 | cy | i16 little-endian | detected center y, pixels |
| 10..11 | dx | i16 little-endian | `cx - setpoint_x`, pixels |
| 12..13 | dy | i16 little-endian | `cy - setpoint_y`, pixels |
| 14 | confidence | u8 | 0..100 |
| 15 | fps | u8 | camera loop FPS, clamped 0..255 |
| 16 | bcc | u8 | XOR of bytes 2..15 |
| 17..18 | tail | u8 | `0D 0A` |

When the target is lost, MaixCAM2 still sends packets with `found=0`,
`cx=cy=dx=dy=confidence=0`, and current `fps`. This lets TI distinguish target
loss from communication timeout.

The header intentionally does not use F32C's `7A ... 7B` frame markers. Keep
MaixCAM2 on a separate TI UART from the F32C motor bus whenever possible.

## TI-side control recommendation

MaixCAM2 should not send gimbal angles. It only sends image error (`dx`, `dy`).
The TI board has motor feedback, speed/position limits, and WHEELTEC F32C frame
output, so it should convert pixels to motor commands there.

For the current F32C TI example, position mode is natural:

```c
if (vision_found) {
    int16_t yaw_delta_x10 = clamp((int16_t)(KX * dx), -YAW_STEP_LIMIT_X10, YAW_STEP_LIMIT_X10);
    int16_t pit_delta_x10 = clamp((int16_t)(KY * dy), -PIT_STEP_LIMIT_X10, PIT_STEP_LIMIT_X10);
    Motor1_T_Position += yaw_delta_x10;
    Motor2_T_Position += pit_delta_x10;
}
```

F32C multi-turn position commands use `0.1 degree` units in the TI example, so
`Motor*_T_Position` should remain angle times 10. Apply deadzone, direction
sign, angle limits, and communication timeout on the TI side.

## ASCII fallback

For debugging, set `PROTOCOL_MODE = "ascii_v2"`:

```text
@T,seq,found,dx,dy,confidence\n
```

Legacy mode is still available as `ascii_legacy`:

```text
@T,found,dx,dy,confidence\n
```
