from __future__ import annotations

from dataclasses import dataclass, field

from . import geometry
from . import joints as joints_mod
from .hardware import Hardware
from .joints import Joint
from .panel import Panel


@dataclass
class Furniture:
    """Un meuble : un assemblage de panneaux, de joints et de quincaillerie."""

    name: str
    description: str = ""
    panels: list[Panel] = field(default_factory=list)
    hardware: list[Hardware] = field(default_factory=list)
    joints: list[Joint] = field(default_factory=list)

    def add_panel(self, panel: Panel) -> Panel:
        self.panels.append(panel)
        return panel

    def add_hardware(self, item: Hardware) -> Hardware:
        self.hardware.append(item)
        return item

    def add_joint(self, joint: Joint) -> Joint:
        self.joints.append(joint)
        return joint

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

    def joint_hardware(self) -> list[Hardware]:
        """Quincaillerie déduite automatiquement des joints (vis, équerres, tourillons...)."""
        thickness_by_panel = {p.name: p.thickness_mm for p in self.panels}
        return joints_mod.aggregate_hardware(self.joints, thickness_by_panel)

    def all_hardware(self) -> list[Hardware]:
        """Quincaillerie saisie à la main + quincaillerie déduite des joints."""
        return self.hardware + self.joint_hardware()

    def total_wood_cost(self) -> float:
        return sum(p.area_m2 * p.material.price_per_m2 for p in self.panels)

    def total_hardware_cost(self) -> float:
        return sum(h.total_price for h in self.all_hardware())

    def total_cost(self) -> float:
        return self.total_wood_cost() + self.total_hardware_cost()

    def total_wood_area_m2(self) -> float:
        return sum(p.area_m2 for p in self.panels)
