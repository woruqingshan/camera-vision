def bbox_center(bbox):
    if not bbox:
        return 0, 0
    x, y, w, h = bbox
    return int(x + w / 2), int(y + h / 2)


def corners_center(corners):
    if not corners:
        return 0, 0
    sx = 0
    sy = 0
    for x, y in corners:
        sx += x
        sy += y
    return int(sx / len(corners)), int(sy / len(corners))


def estimate_center(bbox=None, corners=None):
    # First MVP: bounding box or quadrilateral average.
    # Later upgrade: Homography-based A4 center projection.
    if corners and len(corners) >= 4:
        return corners_center(corners)
    return bbox_center(bbox)
