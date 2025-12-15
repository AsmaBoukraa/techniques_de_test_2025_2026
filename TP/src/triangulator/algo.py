"""Triangulation 2D (approx. Delaunay) pour le TP.

On implémente un algorithme de type Bowyer–Watson.
"""

from __future__ import annotations

from typing import Sequence, Tuple

Point = Tuple[float, float]
Triangle = Tuple[int, int, int]


# ----------------- utilitaires géométriques -----------------


def _area2(a: Point, b: Point, c: Point) -> float:
    """Retourne 2 * aire orientée du triangle ABC."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _is_collinear(points: Sequence[Point], eps: float = 1e-9) -> bool:
    """Vérifie si tous les points sont (quasi) sur une même droite."""
    if len(points) < 3:
        return True
    a, b = points[0], points[1]
    return all(abs(_area2(a, b, c)) <= eps for c in points[2:])


def _in_circumcircle(p: Point, a: Point, b: Point, c: Point) -> bool:
    """Vérifie si le point p est strictement dans le cercle circonscrit à ABC.

    On utilise la formulation déterminant classique. On suppose ABC en
    orientation CCW (sinon le signe est inversé, cf. aire orientée).
    """
    ax, ay = a[0] - p[0], a[1] - p[1]
    bx, by = b[0] - p[0], b[1] - p[1]
    cx, cy = c[0] - p[0], c[1] - p[1]

    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy

    det = (
        a2 * (bx * cy - cx * by)
        - b2 * (ax * cy - cx * ay)
        + c2 * (ax * by - bx * ay)
    )
    return det > 0.0


# ----------------- algorithme Bowyer–Watson -----------------


def _build_super_triangle(
    points: Sequence[Point]
) -> tuple[Point, Point, Point]:
    """Construit un super-triangle englobant tous les points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    dx = max_x - min_x
    dy = max_y - min_y
    dmax = max(dx, dy) or 1.0
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0

    p1 = (mid_x - 20 * dmax, mid_y - dmax)
    p2 = (mid_x, mid_y + 20 * dmax)
    p3 = (mid_x + 20 * dmax, mid_y - dmax)
    return p1, p2, p3


def delaunay_triangulation(
    points: Sequence[Point], eps: float = 1e-9
) -> list[Triangle]:
    """Retourne la triangulation de Delaunay d'un ensemble de points 2D."""
    n = len(points)
    if n < 3:
        return []
    if _is_collinear(points, eps=eps):
        return []

    pts: list[Point] = list(points)
    st_a, st_b, st_c = _build_super_triangle(points)
    idx_a = len(pts)
    idx_b = idx_a + 1
    idx_c = idx_a + 2
    pts.extend([st_a, st_b, st_c])

    triangles: list[Triangle] = [(idx_a, idx_b, idx_c)]

    for pi in range(n):
        p = pts[pi]

        bad_triangles: list[Triangle] = []
        bad_triangles_set = set()
        for t in triangles:
            ia, ib, ic = t
            a, b, c = pts[ia], pts[ib], pts[ic]

            if abs(_area2(a, b, c)) < eps:
                continue

            if _area2(a, b, c) < 0:
                b_tmp, c_tmp = b, c
                b, c = c_tmp, b_tmp

            if _in_circumcircle(p, a, b, c):
                bad_triangles.append(t)
                bad_triangles_set.add(t)

        edge_counts: dict[tuple[int, int], int] = {}

        for ia, ib, ic in bad_triangles:
            for a_idx, b_idx in [(ia, ib), (ib, ic), (ic, ia)]:
                normalized_edge = tuple(sorted((a_idx, b_idx)))
                edge_counts[normalized_edge] = edge_counts.get(
                    normalized_edge, 0
                ) + 1

        triangles = [t for t in triangles if t not in bad_triangles_set]

        for (ia, ib), count in edge_counts.items():
            if count == 1:
                triangles.append((ia, ib, pi))

    result: list[Triangle] = []
    for ia, ib, ic in triangles:
        if ia >= n or ib >= n or ic >= n:
            continue

        a, b, c = pts[ia], pts[ib], pts[ic]
        if abs(_area2(a, b, c)) <= eps:
            continue

        result.append((ia, ib, ic))

    return result