class DisplayAdapter:
    def __init__(self, enabled=True):
        self.enabled = bool(enabled)
        self.disp = None

    def open(self):
        if not self.enabled:
            return False
        try:
            from maix import display
            self.disp = display.Display()
            return True
        except Exception as exc:
            print("[display] disabled:", exc)
            self.enabled = False
            return False

    def show(self, img):
        if not self.enabled or self.disp is None:
            return False
        try:
            self.disp.show(img)
            return True
        except Exception as exc:
            print("[display] show failed:", exc)
            return False
