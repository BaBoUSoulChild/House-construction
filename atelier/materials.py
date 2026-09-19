from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """Un panneau standard (contreplaqué, MDF, mélaminé...) vendu en plaque."""

    name: str
    thickness_mm: float
    price_per_m2: float
    color: str = "#c9a876"
    sheet_length_mm: float = 2500.0
    sheet_width_mm: float = 1250.0
