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

from dataclasses import dataclass

from . import geometry
from .geometry import Vec3

PROTRUSION_MM = 6.0  # de combien le repère dépasse de la surface, "comme dévissé"


@dataclass(frozen=True)
class Fastener:
    """Une position de fixation approximative, avec sa direction de sortie
    (vecteur unitaire, aligné sur un axe) — utilisée par le viewer pour
    orienter un petit modèle de vis plutôt qu'un simple point plat.
    """

    position_mm: Vec3
    normal: Vec3  # vecteur unitaire, pointant hors du panneau A, vers l'extérieur


def aabb_mm(position_mm: Vec3, size_mm: Vec3, rotation_deg: Vec3) -> tuple[Vec3, Vec3]:
    corners = geometry.obb_corners(position_mm, size_mm, rotation_deg)
    return geometry.bounding_box(corners)


def contact_fasteners_mm(
    aabb_a: tuple[Vec3, Vec3], aabb_b: tuple[Vec3, Vec3], count: int
) -> list[Fastener]:
    """`count` fixations approchant l'emplacement des vis/clous entre deux panneaux.

    `aabb_a` doit être le panneau **traversé** par la vis/le clou (celui où
    on verrait la tête de vis) et `aabb_b` le panneau dans lequel elle est
    plantée (voir la convention `panel_a`/`panel_b` de `Joint`).

    L'axe où le chevauchement est le plus petit est la normale du contact
    (les deux panneaux se touchent selon ce plan). Chaque fixation est
    placée juste au-delà de la surface **extérieure** de panel A le long de
    cet axe (celle qui n'est pas en contact avec panel B), décalée de
    `PROTRUSION_MM` — comme une vis légèrement dévissée, pour qu'elle se
    détache visuellement de la planche au lieu de se fondre dedans. Les
    fixations sont réparties le long de l'axe où le chevauchement est le
    plus grand (la longueur du joint), centrées sur le troisième axe
    (généralement l'épaisseur du panneau B).
    """
    lo_a, hi_a = aabb_a
    lo_b, hi_b = aabb_b
    overlap_lo = tuple(max(lo_a[i], lo_b[i]) for i in range(3))
    overlap_hi = tuple(min(hi_a[i], hi_b[i]) for i in range(3))
    extents = tuple(max(overlap_hi[i] - overlap_lo[i], 0.0) for i in range(3))
    center = list((overlap_lo[i] + overlap_hi[i]) / 2 for i in range(3))

    axes_by_extent = sorted(range(3), key=lambda i: extents[i])
    normal_axis = axes_by_extent[0]   # perpendiculaire au plan de contact
    spacing_axis = axes_by_extent[2]  # plus grand chevauchement = longueur du joint

    boundary = center[normal_axis]
    a_center = (lo_a[normal_axis] + hi_a[normal_axis]) / 2
    direction = 1.0 if a_center >= boundary else -1.0
    outer_face = hi_a[normal_axis] if direction > 0 else lo_a[normal_axis]
    center[normal_axis] = outer_face + direction * PROTRUSION_MM

    normal = [0.0, 0.0, 0.0]
    normal[normal_axis] = direction

    count = max(1, count)
    span = extents[spacing_axis]
    margin = span * 0.1
    usable_start = center[spacing_axis] - span / 2 + margin
    usable_span = max(span - 2 * margin, 0.0)

    fasteners: list[Fastener] = []
    for i in range(count):
        t = 0.5 if count == 1 else i / (count - 1)
        p = list(center)
        p[spacing_axis] = usable_start + t * usable_span if span > 0 else center[spacing_axis]
        fasteners.append(Fastener(position_mm=tuple(p), normal=tuple(normal)))  # type: ignore[arg-type]
    return fasteners
