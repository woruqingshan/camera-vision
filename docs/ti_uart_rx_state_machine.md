# TI UART RX State Machine For MaixCAM2 Vision

This document describes the recommended MaixCAM2 -> TI protocol and the TI-side
receiver implementation plan for controlling the WHEELTEC F32C gimbal.

Current architecture:

```text
MaixCAM2 camera vision  --UART-->  TI MSPM0G3507  --UART1/F32C protocol-->  F32C gimbal
                              pixel dx/dy              angle/speed command
```

Important rule: keep the MaixCAM2 UART separate from the F32C motor UART. In the
current TI example, UART1 is already used for the F32C bus and parses `7A ... 7B`
feedback frames. Do not mix MaixCAM2 frames into UART1 unless there is no other
choice.

## 1. Physical Wiring

Recommended one-way wiring:

```text
MaixCAM2 A21 / UART4_TX  ->  TI independent UART_RX
MaixCAM2 GND             ->  TI GND
```

Optional two-way wiring for future debug/configuration:

```text
TI independent UART_TX   ->  MaixCAM2 A22 / UART4_RX
```

Current MaixCAM2 config:

```python
UART_DEVICE = "/dev/ttyS4"
UART_BAUDRATE = 115200
UART_TX_PIN = "A21"
UART_RX_PIN = "A22"
PROTOCOL_MODE = "binary_v1"
TARGET_SEND_HZ = 50
```

UART electrical level should match both boards, normally 3.3 V TTL. Common GND
is mandatory.

## 2. Why Binary Protocol

The earlier ASCII protocol was:

```text
@T,seq,found,dx,dy,confidence\n
```

It is easy to inspect but not ideal for TI closed-loop control because the TI
side has to parse commas, signs and decimal text. The optimized protocol is fixed
length binary:

- fixed 19 bytes per packet;
- no dynamic string parsing;
- one XOR BCC checksum, similar to F32C's BCC idea;
- packet has distinct `A5 5A` header and `0D 0A` tail;
- does not conflict with F32C's `7A ... 7B` frames;
- includes `seq` and `fps` for timeout and health checks;
- includes `found` and `stable` flags for control gating.

At 50 Hz, the bandwidth is tiny:

```text
19 bytes * 50 Hz = 950 bytes/s
```

At 115200 baud this is far below the UART capacity.

## 3. Packet Format: binary_v1

Each packet is exactly 19 bytes:

```text
A5 5A 01 seq_lo seq_hi flags cx_lo cx_hi cy_lo cy_hi dx_lo dx_hi dy_lo dy_hi confidence fps bcc 0D 0A
```

Field table:

| Byte | Name | Type | Description |
| --- | --- | --- | --- |
| 0 | head0 | u8 | fixed `0xA5` |
| 1 | head1 | u8 | fixed `0x5A` |
| 2 | type | u8 | fixed `0x01`, target frame |
| 3 | seq_lo | u8 | low byte of frame counter |
| 4 | seq_hi | u8 | high byte of frame counter |
| 5 | flags | u8 | bit0 found, bit1 stable |
| 6 | cx_lo | u8 | target center x low byte |
| 7 | cx_hi | u8 | target center x high byte |
| 8 | cy_lo | u8 | target center y low byte |
| 9 | cy_hi | u8 | target center y high byte |
| 10 | dx_lo | u8 | x error low byte |
| 11 | dx_hi | u8 | x error high byte |
| 12 | dy_lo | u8 | y error low byte |
| 13 | dy_hi | u8 | y error high byte |
| 14 | confidence | u8 | 0..100 |
| 15 | fps | u8 | MaixCAM2 measured FPS, 0..255 |
| 16 | bcc | u8 | XOR of bytes 2..15 |
| 17 | tail0 | u8 | fixed `0x0D` |
| 18 | tail1 | u8 | fixed `0x0A` |

Endian:

- `seq` is unsigned 16-bit little-endian.
- `cx`, `cy`, `dx`, `dy` are signed 16-bit little-endian.

Coordinate meaning:

```text
cx = detected target center x, pixel coordinate
cy = detected target center y, pixel coordinate
dx = cx - setpoint_x
dy = cy - setpoint_y
```

The current camera resolution is 160x120, so if the setpoint is image center:

```text
setpoint_x = 80
setpoint_y = 60
```

Control interpretation:

- `dx > 0`: target is to the right of setpoint.
- `dx < 0`: target is to the left of setpoint.
- `dy > 0`: target is below setpoint, because image y increases downward.
- `dy < 0`: target is above setpoint.

The actual yaw/pitch sign depends on your gimbal installation and laser/camera
mount direction. Keep sign constants on TI, for example:

```c
#define VISION_YAW_DIR    (+1)   // change to -1 if yaw moves opposite
#define VISION_PITCH_DIR  (+1)   // change to -1 if pitch moves opposite
```

Flags:

```text
bit0 found:  1 means target detected, 0 means target lost
bit1 stable: 1 means confidence >= 60
```

Lost target packet:

```text
found = 0
cx = 0
cy = 0
dx = 0
dy = 0
confidence = 0
fps = current camera loop FPS
```

A lost packet still proves the camera and UART are alive. If no valid packet is
received for a timeout period, that is a communication failure or MaixCAM2 stop.

## 4. Example Packets

Example target packet:

```text
A5 5A 01 01 00 03 5C 00 3A 00 0C 00 F8 FF 5C 3C 0E 0D 0A
```

Decoded:

```text
seq = 1
found = 1
stable = 1
cx = 92
cy = 58
dx = 12
dy = -8
confidence = 92
fps = 60
```

Example lost packet:

```text
A5 5A 01 02 00 00 00 00 00 00 00 00 00 00 00 3C 3F 0D 0A
```

Decoded:

```text
seq = 2
found = 0
stable = 0
cx = 0
cy = 0
dx = 0
dy = 0
confidence = 0
fps = 60
```

## 5. TI SysConfig Modification

Current project already uses UART1 for F32C:

```c
#define UART_1_INST UART1
#define GPIO_UART_1_TX_PIN DL_GPIO_PIN_6
#define GPIO_UART_1_RX_PIN DL_GPIO_PIN_7
```

Add another UART in SysConfig, for example `UART_0` or `UART_2` depending on the
available board pins.

Recommended settings:

```text
Baud rate: 115200
Data bits: 8
Parity: none
Stop bits: 1
RX interrupt: enabled
TX: optional, not required for one-way vision
RX pull-up: enabled if the board needs it
```

After SysConfig generation, you should have generated macros similar to:

```c
#define UART_VISION_INST              UART0
#define UART_VISION_INST_IRQHandler   UART0_IRQHandler
#define UART_VISION_INST_INT_IRQN     UART0_INT_IRQn
```

The exact names depend on your SysConfig instance name. If SysConfig generates
`UART_0_INST`, use that name in the code below or create aliases:

```c
#define UART_VISION_INST              UART_0_INST
#define UART_VISION_INST_IRQHandler   UART_0_INST_IRQHandler
#define UART_VISION_INST_INT_IRQN     UART_0_INST_INT_IRQN
```

Initialize and enable the interrupt in `main()` after `SYSCFG_DL_init()`:

```c
DL_UART_Main_enableInterrupt(UART_VISION_INST, DL_UART_MAIN_INTERRUPT_RX);
NVIC_ClearPendingIRQ(UART_VISION_INST_INT_IRQN);
NVIC_EnableIRQ(UART_VISION_INST_INT_IRQN);
```

Do not remove the existing UART1 initialization because UART1 still controls the
F32C gimbal.

## 6. TI Receiver Data Structure

Create `vision_uart.h`:

```c
#ifndef VISION_UART_H
#define VISION_UART_H

#include <stdint.h>
#include <stdbool.h>

#define VISION_PKT_LEN        19u
#define VISION_HEAD0          0xA5u
#define VISION_HEAD1          0x5Au
#define VISION_TAIL0          0x0Du
#define VISION_TAIL1          0x0Au
#define VISION_TYPE_TARGET    0x01u

#define VISION_FLAG_FOUND     0x01u
#define VISION_FLAG_STABLE    0x02u

typedef struct {
    uint16_t seq;
    uint8_t flags;
    int16_t cx;
    int16_t cy;
    int16_t dx;
    int16_t dy;
    uint8_t confidence;
    uint8_t fps;
    volatile uint8_t updated;
    volatile uint32_t valid_count;
    volatile uint32_t checksum_error_count;
    volatile uint32_t frame_error_count;
} VisionTarget_t;

extern volatile VisionTarget_t g_vision_target;

void Vision_UART_ParseByte(uint8_t byte);
bool Vision_Target_Copy(VisionTarget_t *out);

#endif
```

Create `vision_uart.c`:

```c
#include "vision_uart.h"

volatile VisionTarget_t g_vision_target = {0};

static uint8_t s_buf[VISION_PKT_LEN];
static uint8_t s_idx = 0;

static uint8_t vision_bcc(const uint8_t *data, uint8_t start, uint8_t end_exclusive)
{
    uint8_t bcc = 0;
    uint8_t i;

    for (i = start; i < end_exclusive; i++) {
        bcc ^= data[i];
    }
    return bcc;
}

static uint16_t read_u16_le(const uint8_t *p)
{
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static int16_t read_i16_le(const uint8_t *p)
{
    return (int16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static void parse_complete_packet(const uint8_t *p)
{
    uint8_t calc_bcc;

    if (p[0] != VISION_HEAD0 || p[1] != VISION_HEAD1 ||
        p[17] != VISION_TAIL0 || p[18] != VISION_TAIL1 ||
        p[2] != VISION_TYPE_TARGET) {
        g_vision_target.frame_error_count++;
        return;
    }

    calc_bcc = vision_bcc(p, 2, 16);  // XOR type through fps
    if (calc_bcc != p[16]) {
        g_vision_target.checksum_error_count++;
        return;
    }

    g_vision_target.seq = read_u16_le(&p[3]);
    g_vision_target.flags = p[5];
    g_vision_target.cx = read_i16_le(&p[6]);
    g_vision_target.cy = read_i16_le(&p[8]);
    g_vision_target.dx = read_i16_le(&p[10]);
    g_vision_target.dy = read_i16_le(&p[12]);
    g_vision_target.confidence = p[14];
    g_vision_target.fps = p[15];
    g_vision_target.updated = 1;
    g_vision_target.valid_count++;
}

void Vision_UART_ParseByte(uint8_t byte)
{
    if (s_idx == 0) {
        if (byte != VISION_HEAD0) {
            return;
        }
        s_buf[s_idx++] = byte;
        return;
    }

    if (s_idx == 1) {
        if (byte == VISION_HEAD1) {
            s_buf[s_idx++] = byte;
        } else if (byte == VISION_HEAD0) {
            s_buf[0] = byte;
            s_idx = 1;
        } else {
            s_idx = 0;
        }
        return;
    }

    s_buf[s_idx++] = byte;

    if (s_idx >= VISION_PKT_LEN) {
        parse_complete_packet(s_buf);
        s_idx = 0;
    }
}

bool Vision_Target_Copy(VisionTarget_t *out)
{
    if (out == 0) {
        return false;
    }

    __disable_irq();
    *out = g_vision_target;
    g_vision_target.updated = 0;
    __enable_irq();

    return true;
}
```

This parser does not block inside the interrupt. It only accepts complete frames
with valid header, tail, type and BCC. If bytes are lost or shifted, it searches
for the next `A5 5A` header.

## 7. TI UART ISR Integration

Add a new ISR for the independent vision UART. The exact function name must
match SysConfig.

Example if the generated instance is `UART_0_INST`:

```c
#include "vision_uart.h"

void UART_0_INST_IRQHandler(void)
{
    uint8_t rx;

    if (DL_UART_Main_getPendingInterrupt(UART_0_INST) == DL_UART_MAIN_IIDX_RX) {
        rx = DL_UART_Main_receiveData(UART_0_INST);
        Vision_UART_ParseByte(rx);
    }
}
```

If SysConfig generates `UART0_IRQHandler` directly, use:

```c
void UART0_IRQHandler(void)
{
    uint8_t rx;

    if (DL_UART_Main_getPendingInterrupt(UART0) == DL_UART_MAIN_IIDX_RX) {
        rx = DL_UART_Main_receiveData(UART0);
        Vision_UART_ParseByte(rx);
    }
}
```

Keep the existing `UART_1_INST_IRQHandler()` unchanged for F32C feedback.

## 8. Control Loop Strategy

Do not convert pixels to angles on MaixCAM2. The TI board should do that because
it has:

- motor feedback position;
- F32C output protocol;
- gimbal angle limits;
- control loop timing;
- stop/timeout handling.

The F32C example uses position mode, where target position is signed angle times
10:

```text
Motor1_T_Position unit = 0.1 degree
Motor2_T_Position unit = 0.1 degree
```

A practical first controller is incremental P control:

```c
#define VISION_DEADZONE_PX          3
#define VISION_TIMEOUT_TICKS        50
#define VISION_MIN_CONFIDENCE       40

#define VISION_YAW_DIR              (+1)
#define VISION_PITCH_DIR            (+1)

#define YAW_K_X10_PER_PX            0.8f
#define PITCH_K_X10_PER_PX          0.8f

#define YAW_STEP_LIMIT_X10          8
#define PITCH_STEP_LIMIT_X10        8

#define YAW_MIN_X10                 (-900)
#define YAW_MAX_X10                 (900)
#define PITCH_MIN_X10               (-300)
#define PITCH_MAX_X10               (300)
```

Helper functions:

```c
static int clamp_int(int v, int lo, int hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static int deadzone(int v, int zone)
{
    if (v > -zone && v < zone) return 0;
    return v;
}
```

Control update example:

```c
void Vision_Control_Update(void)
{
    static uint32_t last_valid_count = 0;
    static uint32_t lost_ticks = 0;
    VisionTarget_t v;
    int dx;
    int dy;
    int yaw_step;
    int pitch_step;

    Vision_Target_Copy(&v);

    if (v.valid_count != last_valid_count) {
        last_valid_count = v.valid_count;
        lost_ticks = 0;
    } else {
        lost_ticks++;
    }

    if (lost_ticks > VISION_TIMEOUT_TICKS) {
        // Communication timeout: hold current target or slowly return to center.
        return;
    }

    if ((v.flags & VISION_FLAG_FOUND) == 0 || v.confidence < VISION_MIN_CONFIDENCE) {
        // Camera alive but target not reliable. Hold position.
        return;
    }

    dx = deadzone(v.dx, VISION_DEADZONE_PX);
    dy = deadzone(v.dy, VISION_DEADZONE_PX);

    yaw_step = (int)(VISION_YAW_DIR * YAW_K_X10_PER_PX * dx);
    pitch_step = (int)(VISION_PITCH_DIR * PITCH_K_X10_PER_PX * dy);

    yaw_step = clamp_int(yaw_step, -YAW_STEP_LIMIT_X10, YAW_STEP_LIMIT_X10);
    pitch_step = clamp_int(pitch_step, -PITCH_STEP_LIMIT_X10, PITCH_STEP_LIMIT_X10);

    Motor1_T_Position = clamp_int(Motor1_T_Position + yaw_step, YAW_MIN_X10, YAW_MAX_X10);
    Motor2_T_Position = clamp_int(Motor2_T_Position + pitch_step, PITCH_MIN_X10, PITCH_MAX_X10);
}
```

Call `Vision_Control_Update()` periodically before sending the F32C position
frames. In the current `empty.c`, the simplest place is near the top of the
`while (1)` loop before building `motor*_Position_data_task`.

## 9. Important Issue In Existing TI Code

If your project has a timer interrupt or control file that repeatedly sets:

```c
Motor1_T_Position = 0;
Motor2_T_Position = 0;
```

remove or gate that logic. Otherwise the vision controller will update the target
position and the timer will immediately overwrite it back to zero.

## 10. First Bring-up Procedure

1. Keep the gimbal disabled or disconnected.
2. Run MaixCAM2 and confirm it sends binary frames.
3. On TI, count `g_vision_target.valid_count` and display it on OLED or watch in debugger.
4. Move the target and confirm `dx/dy` signs change as expected.
5. Enable F32C but set very small step limits, for example `2` to `4` x0.1 deg per update.
6. Test yaw only. If it moves away from the target, flip `VISION_YAW_DIR`.
7. Test pitch only. If it moves away from the target, flip `VISION_PITCH_DIR`.
8. Enable both axes.
9. Increase gains slowly.
10. Add timeout behavior after basic tracking is stable.

## 11. Recommended Safety Defaults

Use conservative values first:

```c
VISION_DEADZONE_PX = 3 to 5
VISION_MIN_CONFIDENCE = 40 to 60
YAW_STEP_LIMIT_X10 = 4 to 8
PITCH_STEP_LIMIT_X10 = 4 to 8
YAW_K_X10_PER_PX = 0.3 to 1.0
PITCH_K_X10_PER_PX = 0.3 to 1.0
```

If the laser oscillates around the target:

- increase deadzone;
- reduce `K`;
- reduce per-update step limit;
- lower control update rate;
- optionally add D term using previous `dx/dy`.

If it follows too slowly:

- increase `K` slightly;
- increase step limit;
- raise MaixCAM2 send rate or TI control update rate, but only after signs and
  limits are correct.

## 12. ASCII Debug Fallback

If binary parsing is not ready, set MaixCAM2:

```python
PROTOCOL_MODE = "ascii_v2"
```

Then it sends:

```text
@T,seq,found,dx,dy,confidence\n
```

Use ASCII only for bring-up. For final closed-loop control, use `binary_v1`.
