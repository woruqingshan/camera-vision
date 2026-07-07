from configs import detector_config as cfg
from vision.center_estimator import estimate_center
from vision.confidence import compute_confidence
from vision.types import TargetResult


def _call_or_attr(obj, name, default=None):
    value = getattr(obj, name, default)
    if callable(value):
        try:
            return value()
        except TypeError:
            return default
    return value


def _blob_bbox(blob):
    # Compatible with OpenMV-like/Maix blob objects and tuple-like objects.
    x = _call_or_attr(blob, "x")
    y = _call_or_attr(blob, "y")
    w = _call_or_attr(blob, "w")
    h = _call_or_attr(blob, "h")
    if None not in (x, y, w, h):
        return int(x), int(y), int(w), int(h)
    try:
        return int(blob[0]), int(blob[1]), int(blob[2]), int(blob[3])
    except Exception:
        return None


def _blob_pixels(blob, bbox):
    pixels = _call_or_attr(blob, "pixels")
    if pixels is not None:
        return int(pixels)
    if bbox:
        return int(bbox[2] * bbox[3])
    return 0


def _bbox_corners(bbox):
    x, y, w, h = bbox
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _join_notes(primary, fallback):
    return "maix=[%s]; opencv=[%s]" % (primary.note, fallback.note)


class BlackBorderDetector:
    def __init__(self, image_width, image_height, setpoint_x, setpoint_y):
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.image_area = max(1, self.image_width * self.image_height)
        self.setpoint_x = int(setpoint_x)
        self.setpoint_y = int(setpoint_y)
        self.last_cx = None
        self.last_cy = None
        self._opencv_modules = None
        self._opencv_unavailable_note = ""

    def detect(self, img):
        maix_result = self._detect_with_maix_blobs(img)
        result = maix_result
        if (not maix_result.found) and cfg.ENABLE_OPENCV_FALLBACK:
            fallback_result = self._detect_with_opencv(img)
            if fallback_result.found:
                fallback_result.note = "fallback after maix=[%s]; %s" % (
                    maix_result.note, fallback_result.note)
                result = fallback_result
            else:
                # Do not hide the original Maix failure behind the fallback.
                result = TargetResult(
                    False,
                    method="maix+opencv",
                    note=_join_notes(maix_result, fallback_result),
                )
        if result.found:
            result.dx = int(result.cx - self.setpoint_x)
            result.dy = int(result.cy - self.setpoint_y)
            self.last_cx = result.cx
            self.last_cy = result.cy
        return result

    def _detect_with_maix_blobs(self, img):
        try:
            kwargs = {
                "pixels_threshold": cfg.MIN_PIXELS_THRESHOLD,
                "area_threshold": cfg.MIN_AREA_THRESHOLD,
                "merge": cfg.MERGE_BLOBS,
            }
            if cfg.ROI is not None:
                kwargs["roi"] = cfg.ROI
            try:
                blobs = img.find_blobs([cfg.BLACK_LAB_THRESHOLD], **kwargs)
            except TypeError:
                # Some firmware versions may not accept all keyword args.
                blobs = img.find_blobs([cfg.BLACK_LAB_THRESHOLD])
        except Exception as exc:
            return TargetResult(False, method="maix_find_blobs", note="find_blobs failed: %s" % exc)

        if not blobs:
            return TargetResult(False, method="maix_find_blobs", note="no blob")

        best = None
        best_score = -1
        rejected_bbox = 0
        rejected_size = 0
        rejected_area = 0
        rejected_aspect = 0
        candidate_notes = []
        max_notes = max(0, int(getattr(cfg, "DIAGNOSTIC_MAX_CANDIDATES", 4)))
        for index, blob in enumerate(blobs):
            bbox = _blob_bbox(blob)
            if not bbox:
                rejected_bbox += 1
                continue
            x, y, w, h = bbox
            if w <= 0 or h <= 0:
                rejected_size += 1
                continue
            bbox_area = w * h
            area_ratio = bbox_area / float(self.image_area)
            if area_ratio < cfg.MIN_AREA_RATIO or area_ratio > cfg.MAX_AREA_RATIO:
                rejected_area += 1
                if len(candidate_notes) < max_notes:
                    candidate_notes.append(
                        "#%d bbox=%s area=%.3f reject=area" % (index, bbox, area_ratio))
                continue
            aspect = max(w, h) / float(max(1, min(w, h)))
            if aspect < cfg.MIN_ASPECT or aspect > cfg.MAX_ASPECT:
                rejected_aspect += 1
                if len(candidate_notes) < max_notes:
                    candidate_notes.append(
                        "#%d bbox=%s area=%.3f aspect=%.2f reject=aspect" % (
                            index, bbox, area_ratio, aspect))
                continue
            cx, cy = estimate_center(bbox=bbox, corners=None)
            jump = 0
            if self.last_cx is not None:
                dx = cx - self.last_cx
                dy = cy - self.last_cy
                jump = int((dx * dx + dy * dy) ** 0.5)
            conf = compute_confidence(area_ratio, aspect, cfg.PREFERRED_ASPECT, jump, cfg.MAX_CENTER_JUMP_PX)
            pixels = _blob_pixels(blob, bbox)
            if len(candidate_notes) < max_notes:
                candidate_notes.append(
                    "#%d bbox=%s area=%.3f aspect=%.2f pixels=%d conf=%d" % (
                        index, bbox, area_ratio, aspect, pixels, conf))
            score = conf * 100000 + pixels
            if score > best_score:
                best_score = score
                best = (bbox, cx, cy, bbox_area, conf, aspect)

        if best is None:
            note = "blobs=%d rejected(bbox=%d,size=%d,area=%d,aspect=%d)" % (
                len(blobs), rejected_bbox, rejected_size, rejected_area, rejected_aspect)
            if candidate_notes:
                note += " candidates: " + "; ".join(candidate_notes)
            return TargetResult(False, method="maix_find_blobs", note=note)

        bbox, cx, cy, area, conf, _aspect = best
        if conf < cfg.MIN_CONFIDENCE:
            return TargetResult(False, cx, cy, confidence=conf, bbox=bbox, area=area,
                                method="maix_find_blobs",
                                note="low confidence=%d; %s" % (
                                    conf, "; ".join(candidate_notes)))
        return TargetResult(True, cx, cy, confidence=conf, bbox=bbox, corners=_bbox_corners(bbox),
                            area=area, method="maix_find_blobs", note="bbox center MVP")

    def _detect_with_opencv(self, img):
        # Best-effort fallback. Maix native APIs are still preferred.
        if self._opencv_unavailable_note:
            return TargetResult(False, method="opencv", note=self._opencv_unavailable_note)
        if self._opencv_modules is None:
            try:
                import cv2
                import numpy as np
                self._opencv_modules = (cv2, np)
            except Exception as exc:
                self._opencv_unavailable_note = "opencv unavailable: %s" % exc
                return TargetResult(False, method="opencv", note=self._opencv_unavailable_note)
        cv2, np = self._opencv_modules

        frame = None
        for name in ("to_cv2", "to_numpy", "numpy"):
            method = getattr(img, name, None)
            if callable(method):
                try:
                    frame = method()
                    break
                except Exception:
                    pass
        if frame is None:
            try:
                frame = np.array(img)
            except Exception as exc:
                return TargetResult(False, method="opencv", note="image conversion failed: %s" % exc)

        try:
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = frame
            _, mask = cv2.threshold(gray, cfg.OPENCV_BLACK_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
            contours, _hier = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        except Exception as exc:
            return TargetResult(False, method="opencv", note="cv operation failed: %s" % exc)

        best = None
        best_score = -1
        rejected_area = 0
        rejected_aspect = 0
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w <= 0 or h <= 0:
                continue
            bbox_area = w * h
            area_ratio = bbox_area / float(self.image_area)
            if area_ratio < cfg.MIN_AREA_RATIO or area_ratio > cfg.MAX_AREA_RATIO:
                rejected_area += 1
                continue
            aspect = max(w, h) / float(max(1, min(w, h)))
            if aspect < cfg.MIN_ASPECT or aspect > cfg.MAX_ASPECT:
                rejected_aspect += 1
                continue
            cx, cy = estimate_center(bbox=(x, y, w, h), corners=None)
            jump = 0
            if self.last_cx is not None:
                jump = int(((cx - self.last_cx) ** 2 + (cy - self.last_cy) ** 2) ** 0.5)
            conf = compute_confidence(area_ratio, aspect, cfg.PREFERRED_ASPECT, jump, cfg.MAX_CENTER_JUMP_PX)
            score = conf * 100000 + bbox_area
            if score > best_score:
                best_score = score
                best = ((x, y, w, h), cx, cy, bbox_area, conf)

        if best is None:
            return TargetResult(
                False,
                method="opencv",
                note="contours=%d rejected(area=%d,aspect=%d)" % (
                    len(contours), rejected_area, rejected_aspect),
            )
        bbox, cx, cy, area, conf = best
        if conf < cfg.MIN_CONFIDENCE:
            return TargetResult(False, cx, cy, confidence=conf, bbox=bbox, area=area,
                                method="opencv", note="low confidence")
        return TargetResult(True, cx, cy, confidence=conf, bbox=bbox, corners=_bbox_corners(bbox),
                            area=area, method="opencv", note="fallback bbox center")
