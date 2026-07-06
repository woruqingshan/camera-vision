# UART configuration for MaixCAM2 -> TI Bridge.
# Official MaixPy UART documentation lists MaixCAM2 A21/A22 as UART4 TX/RX with
# device /dev/ttyS4. Verify with your actual board silkscreen and official example.

UART_ENABLED = True
UART_DEVICE = "/dev/ttyS4"
UART_BAUDRATE = 115200

# Pin mapping. Set ENABLE_PINMAP = False if these pins are already mapped by your image.
ENABLE_PINMAP = True
UART_TX_PIN = "A21"
UART_RX_PIN = "A22"
UART_TX_FUNC = "UART4_TX"
UART_RX_FUNC = "UART4_RX"

# First version is one-way: MaixCAM2 TX -> TI Bridge RX, common GND.
NEED_RX = False

# Protocol mode.
# V2 sends: @T,seq,found,dx,dy,confidence\n
# Legacy mode sends: @T,found,dx,dy,confidence\n
INCLUDE_SEQUENCE = True
SEND_DEBUG_FRAME = False

# Send target data at a limited rate so UART and TI parser stay stable.
TARGET_SEND_HZ = 25

# If UART init fails, keep vision loop running and print messages to console.
ALLOW_CONSOLE_FALLBACK = True
