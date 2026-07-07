from maix import image
import cv2
import numpy as np
from vision.types import TargetResult


FRAME_W = 160
FRAME_H = 120

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

params = {
    "area_min": 50,
    "area_max_ratio": 0.62,
    "border_margin": 2,
    "epsilon_ratio": 0.045,
    "aspect_min": 1.0,
    "aspect_max": 3.4,
    "center_pair_tolerance": 9,
    "track_radius": 38,
    "smooth_alpha": 0.35,
    "max_lost_keep": 8,
}


def order_points(vertices):
    pts = vertices.astype(np.float32)
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = pts[:, 0] - pts[:, 1]
    rect[0] = pts[np.argmin(s)]
    rect[1] = pts[np.argmax(d)]
    rect[2] = pts[np.argmax(s)]
    rect[3] = pts[np.argmin(d)]
    return rect


def line_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-6:
        return None

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) -
          (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) -
          (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return np.array([px, py], dtype=np.float32)


def quad_center(rect):
    center = line_intersection(rect[0], rect[2], rect[1], rect[3])
    if center is None:
        center = rect.mean(axis=0)
    return center


def contour_touches_border(x, y, w, h):
    m = params["border_margin"]
    return x <= m or y <= m or x + w >= FRAME_W - m or y + h >= FRAME_H - m


def is_rectangle(vertices):
    rect = order_points(vertices)
    contour = rect.astype(np.int32).reshape(4, 1, 2)
    if not cv2.isContourConvex(contour):
        return False

    area = abs(cv2.contourArea(contour))
    if area < params["area_min"]:
        return False
    if area > FRAME_W * FRAME_H * params["area_max_ratio"]:
        return False

    x, y, w, h = cv2.boundingRect(contour)
    if w <= 0 or h <= 0:
        return False
    if contour_touches_border(x, y, w, h):
        return False

    aspect = max(w, h) / min(w, h)
    if aspect < params["aspect_min"] or aspect > params["aspect_max"]:
        return False

    center = quad_center(rect)
    inside = cv2.pointPolygonTest(contour, (float(center[0]), float(center[1])), False)
    return inside >= 0


def find_best_rectangles(contours):
    candidates = []
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:12]:
        area = cv2.contourArea(cnt)
        if area < params["area_min"]:
            continue

        perimeter = cv2.arcLength(cnt, True)
        epsilon = params["epsilon_ratio"] * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if len(approx) != 4:
            continue

        vertices = approx.reshape(4, 2)
        if not is_rectangle(vertices):
            continue

        rect = order_points(vertices)
        contour = rect.astype(np.int32).reshape(4, 1, 2)
        x, y, w, h = cv2.boundingRect(contour)
        candidates.append({
            "rect": rect,
            "center": quad_center(rect),
            "area": abs(cv2.contourArea(contour)),
            "bbox": (x, y, w, h),
        })

    candidates.sort(key=lambda item: item["area"], reverse=True)
    return candidates


def pick_outer_candidate(candidates, prev_center):
    if not candidates:
        return None
    if prev_center is None:
        return candidates[0]

    radius2 = params["track_radius"] ** 2
    near = []
    for cand in candidates:
        diff = cand["center"] - prev_center
        d2 = diff[0] * diff[0] + diff[1] * diff[1]
        if d2 <= radius2:
            near.append((d2, cand))

    if near:
        near.sort(key=lambda item: (-item[1]["area"], item[0]))
        return near[0][1]
    return candidates[0]


def choose_border_center(candidates, prev_center):
    outer = pick_outer_candidate(candidates, prev_center)
    if outer is None:
        return None, None, None

    best_inner = None
    tol2 = params["center_pair_tolerance"] ** 2

    for cand in candidates:
        if cand is outer:
            continue
        if cand["area"] >= outer["area"] * 0.92:
            continue
        diff = cand["center"] - outer["center"]
        if diff[0] * diff[0] + diff[1] * diff[1] <= tol2:
            best_inner = cand
            break

    if best_inner is not None:
        center = (outer["center"] + best_inner["center"]) * 0.5
        return center, outer["rect"], best_inner["rect"]

    return outer["center"], outer["rect"], None


class BlackBorderDetector:
    def __init__(self, image_width, image_height, setpoint_x, setpoint_y):
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.setpoint_x = int(setpoint_x)
        self.setpoint_y = int(setpoint_y)
        self.last_center = None
        self.lost_count = 0

    def detect(self, img):
        img_cv = image.image2cv(img, copy=False)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        center = None
        vertices = None
        inner_vertices = None

        if contours:
            candidates = find_best_rectangles(contours)
            center_f, vertices, inner_vertices = choose_border_center(candidates, self.last_center)
            if center_f is not None:
                if self.last_center is not None:
                    alpha = params["smooth_alpha"]
                    center_f = self.last_center * (1.0 - alpha) + center_f * alpha
                self.last_center = center_f
                self.lost_count = 0
                center = (int(round(center_f[0])), int(round(center_f[1])))
            else:
                self.lost_count += 1
        else:
            self.lost_count += 1

        if self.lost_count > params["max_lost_keep"]:
            self.last_center = None

        if vertices is not None and center is not None:
            vertices_i = vertices.astype(np.int32)
            for (x, y) in vertices_i:
                cv2.circle(img_cv, (x, y), 3, (0, 0, 255), -1)
            cv2.drawContours(img_cv, [vertices_i.reshape(4, 1, 2)], -1, (0, 255, 0), 2)
            if inner_vertices is not None:
                inner_i = inner_vertices.astype(np.int32)
                cv2.drawContours(img_cv, [inner_i.reshape(4, 1, 2)], -1, (0, 255, 255), 1)
            img.draw_cross(center[0], center[1], image.COLOR_BLUE)
            status = "Rect: (%d,%d)" % (center[0], center[1])
            x, y, w, h = cv2.boundingRect(vertices_i.reshape(4, 1, 2))
            corners = [(int(px), int(py)) for px, py in vertices_i]
            result = TargetResult(
                True,
                center[0],
                center[1],
                dx=int(center[0] - self.setpoint_x),
                dy=int(center[1] - self.setpoint_y),
                confidence=90,
                bbox=(int(x), int(y), int(w), int(h)),
                corners=corners,
                area=int(abs(cv2.contourArea(vertices_i.reshape(4, 1, 2)))),
                method="lasttestfirst",
                note=status,
            )
            if inner_vertices is not None:
                result.inner_corners = [(int(px), int(py)) for px, py in inner_i]
            else:
                result.inner_corners = []
            result.display_img = image.cv2image(img_cv, copy=False)
            return result

        result = TargetResult(False, method="lasttestfirst", note="No rect")
        result.display_img = image.cv2image(img_cv, copy=False)
        return result
