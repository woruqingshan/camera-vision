from configs import serial_config as cfg


class UartSender:
    def __init__(self):
        self.serial = None
        self.console_fallback = False

    def open(self):
        if not cfg.UART_ENABLED:
            self.console_fallback = True
            return False
        try:
            from maix import uart
            if cfg.ENABLE_PINMAP:
                try:
                    from maix import pinmap, err
                    err.check_raise(pinmap.set_pin_function(cfg.UART_TX_PIN, cfg.UART_TX_FUNC),
                                    "Failed set %s to %s" % (cfg.UART_TX_PIN, cfg.UART_TX_FUNC))
                    if cfg.NEED_RX:
                        err.check_raise(pinmap.set_pin_function(cfg.UART_RX_PIN, cfg.UART_RX_FUNC),
                                        "Failed set %s to %s" % (cfg.UART_RX_PIN, cfg.UART_RX_FUNC))
                    else:
                        # RX is still mapped by default for convenience, but failures are not fatal.
                        try:
                            pinmap.set_pin_function(cfg.UART_RX_PIN, cfg.UART_RX_FUNC)
                        except Exception:
                            pass
                except Exception as pin_exc:
                    print("[uart] pinmap warning:", pin_exc)
            self.serial = uart.UART(cfg.UART_DEVICE, cfg.UART_BAUDRATE)
            return True
        except Exception as exc:
            print("[uart] init failed:", exc)
            if cfg.ALLOW_CONSOLE_FALLBACK:
                self.console_fallback = True
                print("[uart] using console fallback")
                return False
            raise

    def write_line(self, text):
        if not isinstance(text, str):
            text = str(text)
        if self.serial is not None:
            try:
                if hasattr(self.serial, "write_str"):
                    self.serial.write_str(text)
                else:
                    self.serial.write(text.encode())
                return True
            except Exception as exc:
                print("[uart] write failed:", exc)
        if self.console_fallback:
            print(text, end="")
        return False

    def write_bytes(self, data):
        if isinstance(data, str):
            data = data.encode()
        else:
            data = bytes(data)
        if self.serial is not None:
            try:
                self.serial.write(data)
                return True
            except Exception as exc:
                print("[uart] write failed:", exc)
        if self.console_fallback:
            print(" ".join("%02X" % value for value in data))
        return False

    def close(self):
        self.serial = None
