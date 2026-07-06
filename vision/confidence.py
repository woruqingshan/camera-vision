def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def compute_confidence(area_ratio, aspect, preferred_aspect=1.414, jump_px=0, max_jump_px=90):
    # Area confidence: tiny targets are less stable, but huge targets may also be invalid.
    if area_ratio <= 0:
        area_score = 0
    elif area_ratio < 0.03:
        area_score = int(area_ratio / 0.03 * 70)
    elif area_ratio <= 0.45:
        area_score = 90
    else:
        area_score = 75

    # Aspect confidence based on distance from A4 ratio.
    aspect_err = abs(aspect - preferred_aspect)
    aspect_score = int(100 - min(70, aspect_err / preferred_aspect * 100))

    # Continuity penalty.
    jump_penalty = 0
    if max_jump_px > 0 and jump_px > max_jump_px:
        jump_penalty = min(35, int((jump_px - max_jump_px) / max_jump_px * 35))

    score = int(0.50 * area_score + 0.50 * aspect_score - jump_penalty)
    return clamp(score, 0, 100)
