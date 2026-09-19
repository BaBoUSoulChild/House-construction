from __future__ import annotations

from dataclasses import dataclass, field

from . import geometry
from .hardware import Hardware
from .panel import Panel


@dataclass
class Furniture:
    """Un meuble : un assemblage de panneaux + de la quincaillerie."""

    name: str
    description: str = ""
    panels: list[Panel] = field(default_factory=list)
    hardware: list[Hardware] = field(default_factory=list)

    def add_panel(self, panel: Panel) -> Panel:
        self.panels.append(panel)
        return panel

    def add_hardware(self, item: Hardware) -> Hardware:
        self.hardware.append(item)
        return item

    def bounding_box_mm(self) -> tuple[geometry.Vec3, geometry.Vec3]:
        if not self.panels:
            return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        all_corners: list[geometry.Vec3] = []
        for panel in self.panels:
            all_corners.extend(
                geometry.obb_corners(panel.position_mm, panel.size_mm, panel.rotation_deg)
            )
        return geometry.bounding_box(all_corners)

    def overall_size_mm(self) -> geometry.Vec3:
        lo, hi = self.bounding_box_mm()
        return (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])

    def total_wood_cost(self) -> float:
        return sum(p.area_m2 * p.material.price_per_m2 for p in self.panels)

    def total_hardware_cost(self) -> float:
        return sum(h.total_price for h in self.hardware)

    def total_cost(self) -> float:
        return self.total_wood_cost() + self.total_hardware_cost()

    def total_wood_area_m2(self) -> float:
        return sum(p.area_m2 for p in self.panels)
