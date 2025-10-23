import numpy as np
SIEVE_SIZES_MM = [4.75, 2.36, 1.18, 0.6, 0.3, 0.15]

def compute_psd_and_fm(diameters_mm):
    if not diameters_mm:
        return {"fm": None, "percent_passing": {}}
    arr = np.array(diameters_mm)
    n = len(arr)
    percent_passing = {}
    for s in SIEVE_SIZES_MM:
        passing = np.sum(arr <= s)
        percent_passing[s] = float(100.0 * passing / n)
    percent_retained = []
    prev_passing = 100.0
    for s in SIEVE_SIZES_MM:
        cur_passing = percent_passing[s]
        retained = prev_passing - cur_passing
        percent_retained.append(max(0.0, retained))
        prev_passing = cur_passing
    fm = sum(percent_retained) / 100.0
    return {"fm": float(fm), "percent_passing": percent_passing, "percent_retained": percent_retained}