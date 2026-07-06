class TargetResult:
    def __init__(self, found=False, cx=0, cy=0, dx=0, dy=0, confidence=0,
                 bbox=None, corners=None, area=0, method="none", note=""):
        self.found = bool(found)
        self.cx = int(cx)
        self.cy = int(cy)
        self.dx = int(dx)
        self.dy = int(dy)
        self.confidence = int(confidence)
        self.bbox = bbox  # (x, y, w, h)
        self.corners = corners or []
        self.area = int(area)
        self.method = method
        self.note = note

    def __repr__(self):
        return ("TargetResult(found=%s, cx=%d, cy=%d, dx=%d, dy=%d, "
                "confidence=%d, bbox=%s, method=%s)" % (
                    self.found, self.cx, self.cy, self.dx, self.dy,
                    self.confidence, self.bbox, self.method))
