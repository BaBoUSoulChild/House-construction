"""Calcul approximatif de l'endroit où deux panneaux se touchent, pour placer
des marqueurs de quincaillerie en 3D (vis, tourillons...).

Ce n'est PAS un plan de perçage fiable : c'est une approximation basée sur
le chevauchement des boîtes englobantes (AABB) des deux panneaux, qui
suppose qu'ils sont bien positionnés bord à bord (ce qui est le cas dans
un `definition.py` correctement construit). Pour des panneaux orientés à
des angles quelconques (pas des multiples de 90°), l'AABB surestime le
volume réel du panneau et l'approximation devient plus grossière.
"""

from __future__ import annotations

from . import geometry
from .geometry import Vec3


def aabb_mm(position_mm: Vec3, size_mm: Vec3, rotation_deg: Vec3) -> tuple[Vec3, Vec3]:
    corners = geometry.obb_corners(position_mm, size_mm, rotation_deg)
    return geometry.bounding_box(corners)


def contact_points_mm(aabb_a: tuple[Vec3, Vec3], aabb_b: tuple[Vec3, Vec3], count: int) -> list[Vec3]:
    """`count` points répartis le long de la zone de contact entre deux AABB.

    L'axe où le chevauchement est le plus petit est pris comme normale du
    contact (les deux panneaux se touchent selon ce plan) ; les points sont
    répartis le long de l'axe où le chevauchement est le plus grand (la
    longueur du joint), centrés sur le troisième axe.
    """
    lo_a, hi_a = aabb_a
    lo_b, hi_b = aabb_b
    overlap_lo = tuple(max(lo_a[i], lo_b[i]) for i in range(3))
    overlap_hi = tuple(min(hi_a[i], hi_b[i]) for i in range(3))
    extents = tuple(max(overlap_hi[i] - overlap_lo[i], 0.0) for i in range(3))
    center = tuple((overlap_lo[i] + overlap_hi[i]) / 2 for i in range(3))

    axes_by_extent = sorted(range(3), key=lambda i: extents[i])
    spacing_axis = axes_by_extent[2]  # plus grand chevauchement = longueur du joint

    count = max(1, count)
    span = extents[spacing_axis]
    margin = span * 0.1
    usable_start = center[spacing_axis] - span / 2 + margin
    usable_span = max(span - 2 * margin, 0.0)

    points: list[Vec3] = []
    for i in range(count):
        t = 0.5 if count == 1 else i / (count - 1)
        p = list(center)
        p[spacing_axis] = usable_start + t * usable_span if span > 0 else center[spacing_axis]
        points.append(tuple(p))  # type: ignore[arg-type]
    return points
