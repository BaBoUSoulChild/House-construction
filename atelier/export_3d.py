from __future__ import annotations

from .furniture import Furniture


def furniture_to_scene(furniture: Furniture) -> dict:
    """Convertit un Furniture en dict JSON-sérialisable pour le visualiseur three.js.

    Unité de la scène : le mètre (convention standard pour le rendu 3D / AR).
    Rotation : voir `atelier.geometry` (Euler ZYX appliqué au vecteur, à
    charger côté three.js avec `new THREE.Euler(rx, ry, rz, 'ZYX')`).
    """
    panels_json = []
    for p in furniture.panels:
        panels_json.append(
            {
                "name": p.name,
                "size_m": [v / 1000 for v in p.size_mm],
                "position_m": [v / 1000 for v in p.position_mm],
                "rotation_deg": list(p.rotation_deg),
                "color": p.color or p.material.color,
                "material": p.material.name,
                "note": p.note,
            }
        )

    lo_mm, hi_mm = furniture.bounding_box_mm()
    overall_mm = tuple(hi_mm[i] - lo_mm[i] for i in range(3))

    return {
        "name": furniture.name,
        "description": furniture.description,
        "unit": "m",
        "rotation_convention": "euler ZYX applied to vector (three.js: new THREE.Euler(rx, ry, rz, 'ZYX'), angles in radians)",
        "overall_size_mm": list(overall_mm),
        "overall_size_m": [v / 1000 for v in overall_mm],
        "panels": panels_json,
        "hardware": [
            {"name": h.name, "qty": h.qty, "unit_price": h.unit_price, "note": h.note}
            for h in furniture.hardware
        ],
        "total_wood_cost_eur": round(furniture.total_wood_cost(), 2),
        "total_hardware_cost_eur": round(furniture.total_hardware_cost(), 2),
        "total_cost_eur": round(furniture.total_cost(), 2),
        "total_wood_area_m2": round(furniture.total_wood_area_m2(), 3),
    }
