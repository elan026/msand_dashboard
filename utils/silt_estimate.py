def silt_fraction_from_settled_height(settled_mm, total_mm, calibration_factor=1.0):
    if total_mm <= 0:
        return None
    fraction_by_volume = settled_mm / total_mm
    percent_by_mass = fraction_by_volume * 100.0 * calibration_factor
    return float(percent_by_mass)