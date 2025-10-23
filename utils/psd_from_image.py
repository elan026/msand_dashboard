import cv2, numpy as np
from scipy import ndimage

def estimate_particle_sizes(image_bgr, pixels_to_mm, min_particle_px=3):
    img = image_bgr.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    distance = cv2.distanceTransform(opened, cv2.DIST_L2, 3)
    local_max = (distance > (0.4 * distance.max())).astype(np.uint8)
    markers, _ = ndimage.label(local_max)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    diameters_mm = []
    for c in contours:
        area = cv2.contourArea(c)
        if area <= min_particle_px**2:
            continue
        eq_d_px = (4.0 * area / np.pi)**0.5
        eq_d_mm = eq_d_px * (pixels_to_mm if pixels_to_mm else 0.01)
        diameters_mm.append(eq_d_mm)
    return diameters_mm