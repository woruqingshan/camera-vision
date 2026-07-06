from configs import camera_config as cfg


class CameraSource:
    def __init__(self):
        self.cam = None
        self.width = cfg.CAMERA_WIDTH
        self.height = cfg.CAMERA_HEIGHT

    def open(self):
        from maix import camera
        if cfg.CAMERA_FORMAT == "grayscale":
            try:
                from maix import image
                self.cam = camera.Camera(cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT, image.Format.FMT_GRAYSCALE)
            except Exception:
                self.cam = camera.Camera(cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)
        else:
            self.cam = camera.Camera(cfg.CAMERA_WIDTH, cfg.CAMERA_HEIGHT)
        return True

    def read(self):
        if self.cam is None:
            raise RuntimeError("CameraSource is not opened")
        img = self.cam.read()
        return self._apply_orientation(img)

    def _apply_orientation(self, img):
        # MaixPy Image orientation APIs may vary by firmware version. Try common names.
        if cfg.FLIP_X:
            for name in ("flip", "mirror", "hmirror"):
                fn = getattr(img, name, None)
                if callable(fn):
                    try:
                        img = fn(True, False) if name == "flip" else fn()
                        break
                    except Exception:
                        pass
        if cfg.FLIP_Y:
            for name in ("flip", "vflip"):
                fn = getattr(img, name, None)
                if callable(fn):
                    try:
                        img = fn(False, True) if name == "flip" else fn()
                        break
                    except Exception:
                        pass
        if cfg.ROTATE_DEG:
            fn = getattr(img, "rotate", None)
            if callable(fn):
                try:
                    img = fn(cfg.ROTATE_DEG)
                except Exception:
                    pass
        return img

    def close(self):
        self.cam = None
