from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Hardware:
    """Un élément de quincaillerie (vis, charnière, tourillon, équerre...).

    `positions_mm` est optionnel : une position 3D par unité posée (ex. 4
    positions pour 4 roulettes), utilisée uniquement pour l'affichage —
    aucun calcul (coût, quantité) n'en dépend. Laissé vide si la position
    n'est pas connue ou pas pertinente (ex. de la colle).
    """

    name: str
    qty: int
    unit_price: float = 0.0
    note: str = ""
    positions_mm: list[tuple[float, float, float]] = field(default_factory=list)

    @property
    def total_price(self) -> float:
        return self.qty * self.unit_price
