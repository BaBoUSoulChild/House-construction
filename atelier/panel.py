from __future__ import annotations

from dataclasses import dataclass, field

from .materials import Material


@dataclass
class Panel:
    """Un panneau rectangulaire (un élément à découper dans une plaque).

    Convention d'axes (identique à three.js) : Y = hauteur (vertical),
    X et Z forment le plan horizontal (sol). Dimensions locales du panneau
    avant rotation : longueur = X, largeur = Y, épaisseur (= épaisseur du
    matériau) = Z.
    `position_mm` est le centre du panneau dans l'espace du meuble.
    `rotation_deg` est un Euler (rx, ry, rz) en degrés, voir `atelier.geometry`.
    """

    name: str
    length_mm: float
    width_mm: float
    material: Material
    position_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    color: str | None = None
    note: str = ""

    @property
    def thickness_mm(self) -> float:
        return self.material.thickness_mm

    @property
    def size_mm(self) -> tuple[float, float, float]:
        return (self.length_mm, self.width_mm, self.thickness_mm)

    @property
    def area_m2(self) -> float:
        return (self.length_mm * self.width_mm) / 1_000_000
