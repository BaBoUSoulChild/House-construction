from __future__ import annotations

from collections import defaultdict

from . import contact
from .contact import Fastener
from .furniture import Furniture

DEFAULT_NORMAL: tuple[float, float, float] = (0.0, 1.0, 0.0)  # vers le haut, faute de mieux


def _mm_to_m(p: tuple[float, float, float]) -> list[float]:
    return [v / 1000 for v in p]


def _hardware_fasteners_and_panels(
    furniture: Furniture,
) -> tuple[dict[str, list[Fastener]], dict[str, set[str]]]:
    """Pour chaque nom de quincaillerie : les fixations 3D connues (position +
    direction, en mm) et les panneaux impliqués, en combinant les positions
    saisies à la main (`Hardware.positions_mm`, sans direction connue — on
    suppose "vers le haut") et celles déduites des `Joint`.
    """
    fasteners: dict[str, list[Fastener]] = defaultdict(list)
    panels_touched: dict[str, set[str]] = defaultdict(set)

    for h in furniture.hardware:
        for pos in h.positions_mm:
            fasteners[h.name].append(Fastener(position_mm=pos, normal=DEFAULT_NORMAL))

    panels_by_name = {p.name: p for p in furniture.panels}
    for joint in furniture.joints:
        for panel_name in (joint.panel_a, joint.panel_b):
            if panel_name not in panels_by_name:
                raise ValueError(
                    f"Le joint {joint.panel_a!r} ↔ {joint.panel_b!r} référence "
                    f"le panneau {panel_name!r}, introuvable dans furniture.panels "
                    "(vérifiez l'orthographe dans definition.py)."
                )
        panel_a = panels_by_name[joint.panel_a]
        panel_b = panels_by_name[joint.panel_b]
        aabb_a = contact.aabb_mm(panel_a.position_mm, panel_a.size_mm, panel_a.rotation_deg)
        aabb_b = contact.aabb_mm(panel_b.position_mm, panel_b.size_mm, panel_b.rotation_deg)
        thickness = min(panel_a.thickness_mm, panel_b.thickness_mm)

        for hw in joint.hardware_with_glue(thickness):
            fasteners[hw.name].extend(contact.contact_fasteners_mm(aabb_a, aabb_b, hw.qty))
            panels_touched[hw.name].update((joint.panel_a, joint.panel_b))

    return fasteners, panels_touched


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

    fasteners_by_name, panels_by_name = _hardware_fasteners_and_panels(furniture)
    hardware_json = []
    for h in furniture.all_hardware():
        hw_fasteners = fasteners_by_name.get(h.name, [])
        hardware_json.append(
            {
                "name": h.name,
                "qty": h.qty,
                "unit_price": h.unit_price,
                "note": h.note,
                "positions_m": [_mm_to_m(f.position_mm) for f in hw_fasteners],
                "normals": [list(f.normal) for f in hw_fasteners],
                "panels": sorted(panels_by_name.get(h.name, set())),
            }
        )

    return {
        "name": furniture.name,
        "description": furniture.description,
        "unit": "m",
        "rotation_convention": "euler ZYX applied to vector (three.js: new THREE.Euler(rx, ry, rz, 'ZYX'), angles in radians)",
        "overall_size_mm": list(overall_mm),
        "overall_size_m": [v / 1000 for v in overall_mm],
        "panels": panels_json,
        "hardware": hardware_json,
        "total_wood_cost_eur": round(furniture.total_wood_cost(), 2),
        "total_hardware_cost_eur": round(furniture.total_hardware_cost(), 2),
        "total_cost_eur": round(furniture.total_cost(), 2),
        "total_wood_area_m2": round(furniture.total_wood_area_m2(), 3),
    }
