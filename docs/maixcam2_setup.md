# MaixCAM2 Setup Notes

Default UART setup follows the official MaixPy MaixCAM2 example:

```text
A21 -> UART4_TX
A22 -> UART4_RX
Device: /dev/ttyS4
Baudrate: 115200
```

Only TX is required for the first version:

```text
MaixCAM2 TX -> TI Bridge RX
MaixCAM2 GND -> TI Bridge GND
```

If your expansion board exposes different pins, edit `configs/serial_config.py`.

Run order:

```bash
python tools/test_display.py
python tools/test_camera.py
python tools/test_uart.py
python tools/test_detector.py
python main.py
```
