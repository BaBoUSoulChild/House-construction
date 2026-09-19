"""Petites primitives géométriques 3D en Python pur (pas de dépendance numpy).

Convention de rotation : Euler (rx, ry, rz) en degrés, appliquée à un vecteur
colonne comme R = Rz @ Ry @ Rx (ordre intrinsèque X, Y, Z). Le visualiseur
three.js utilise THREE.Euler(rx, ry, rz, 'ZYX') pour rester cohérent.
"""

from __future__ import annotations

import math

Vec3 = tuple[float, float, float]
Mat3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def _deg2rad(d: float) -> float:
    return d * math.pi / 180.0


def _mat_mul(a: Mat3, b: Mat3) -> Mat3:
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )  # type: ignore[return-value]


def _mat_vec(m: Mat3, v: Vec3) -> Vec3:
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def rotation_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> Mat3:
    rx, ry, rz = _deg2rad(rx_deg), _deg2rad(ry_deg), _deg2rad(rz_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rx_m: Mat3 = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    ry_m: Mat3 = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    rz_m: Mat3 = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    return _mat_mul(_mat_mul(rz_m, ry_m), rx_m)


def obb_corners(center: Vec3, size: Vec3, rotation_deg: Vec3) -> list[Vec3]:
    """8 coins d'une boîte orientée (utilisé pour calculer l'encombrement)."""
    r = rotation_matrix(*rotation_deg)
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                local = (sx * hx, sy * hy, sz * hz)
                wx, wy, wz = _mat_vec(r, local)
                corners.append((wx + center[0], wy + center[1], wz + center[2]))
    return corners


def bounding_box(points: list[Vec3]) -> tuple[Vec3, Vec3]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
