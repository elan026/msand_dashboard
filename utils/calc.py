def pixel_to_mm_scale(scale_marker_px_length, marker_real_mm):
    if scale_marker_px_length <= 0:
        return None
    return marker_real_mm / scale_marker_px_length