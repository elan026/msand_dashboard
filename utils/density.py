def compute_bulk_density(mass_g, container_volume_ml):
    if container_volume_ml <= 0:
        return None
    density_g_cm3 = mass_g / container_volume_ml
    density_kg_m3 = density_g_cm3 * 1000.0
    return {"g_cm3": density_g_cm3, "kg_m3": density_kg_m3}

def compute_specific_gravity_particle(M_dry_g, displaced_volume_ml):
    if displaced_volume_ml <= 0:
        return None
    specific_gravity = M_dry_g / displaced_volume_ml
    return float(specific_gravity)