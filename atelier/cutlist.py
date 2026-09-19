"""Plan de débit : regroupement des panneaux + optimisation de découpe (nesting).

L'algorithme de nesting est un "shelf packing" glouton en premier ajustement
décroissant (FFDH) : les panneaux sont triés par plus grande dimension
décroissante, puis placés sur des étagères successives dans chaque plaque de
matériau, avec test des deux orientations (rotation 90°). C'est un heuristique
simple et rapide, pas un bin-packing optimal, mais largement suffisant pour du
débit d'atelier.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .furniture import Furniture
from .materials import Material
from .panel import Panel

KERF_MM_DEFAULT = 3.0  # largeur de la lame de scie


@dataclass
class Placement:
    panel_name: str
    x_mm: float
    y_mm: float
    length_mm: float
    width_mm: float
    rotated: bool


@dataclass
class Sheet:
    length_mm: float
    width_mm: float
    placements: list[Placement] = field(default_factory=list)
    _shelves: list[dict] = field(default_factory=list, repr=False)

    def try_place(self, panel: Panel, kerf_mm: float) -> bool:
        for w, h, rotated in (
            (panel.length_mm, panel.width_mm, False),
            (panel.width_mm, panel.length_mm, True),
        ):
            for shelf in self._shelves:
                if h <= shelf["height"] + 1e-6 and shelf["x_cursor"] + w <= self.length_mm + 1e-6:
                    self.placements.append(Placement(panel.name, shelf["x_cursor"], shelf["y"], w, h, rotated))
                    shelf["x_cursor"] += w + kerf_mm
                    return True
            new_y = sum(s["height"] + kerf_mm for s in self._shelves)
            if new_y + h <= self.width_mm + 1e-6 and w <= self.length_mm + 1e-6:
                self._shelves.append({"y": new_y, "height": h, "x_cursor": w + kerf_mm})
                self.placements.append(Placement(panel.name, 0.0, new_y, w, h, rotated))
                return True
        return False

    def utilization(self) -> float:
        used = sum(p.length_mm * p.width_mm for p in self.placements)
        return used / (self.length_mm * self.width_mm)


def group_panels(furniture: Furniture) -> dict[tuple[str, float, float, float], int]:
    """Regroupe les panneaux identiques (même matériau + mêmes dimensions)."""
    counts: dict[tuple[str, float, float, float], int] = defaultdict(int)
    for p in furniture.panels:
        key = (p.material.name, p.length_mm, p.width_mm, p.thickness_mm)
        counts[key] += 1
    return counts


def pack_material(panels: list[Panel], material: Material, kerf_mm: float = KERF_MM_DEFAULT) -> list[Sheet]:
    ordered = sorted(panels, key=lambda p: max(p.length_mm, p.width_mm), reverse=True)
    sheets: list[Sheet] = []
    for panel in ordered:
        if not any(s.try_place(panel, kerf_mm) for s in sheets):
            sheet = Sheet(material.sheet_length_mm, material.sheet_width_mm)
            if not sheet.try_place(panel, kerf_mm):
                raise ValueError(
                    f"Le panneau '{panel.name}' ({panel.length_mm:.0f}×{panel.width_mm:.0f}mm) "
                    f"ne tient pas dans une plaque de {material.name} "
                    f"({material.sheet_length_mm:.0f}×{material.sheet_width_mm:.0f}mm), "
                    "même seul et pivoté."
                )
            sheets.append(sheet)
    return sheets


def pack_furniture(furniture: Furniture, kerf_mm: float = KERF_MM_DEFAULT) -> dict[str, list[Sheet]]:
    by_material: dict[str, list[Panel]] = defaultdict(list)
    materials_by_name: dict[str, Material] = {}
    for p in furniture.panels:
        by_material[p.material.name].append(p)
        materials_by_name[p.material.name] = p.material
    return {
        name: pack_material(panels, materials_by_name[name], kerf_mm)
        for name, panels in by_material.items()
    }
