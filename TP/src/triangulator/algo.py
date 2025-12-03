"""Triangulation 2D (approx. Delaunay) pour le TP.

On implémente un algorithme de type Bowyer–Watson :

- Si < 3 points ou points colinéaires aucune triangulation possible.
- On crée un SUPER-TRIANGLE qui englobe tous les points.
- On insère les points un par un :
  - On supprime les triangles dont le cercle circonscrit contient le point.
  - On construit le polygone "trou" (arêtes frontières).
  - On crée de nouveaux triangles entre le point courant et chaque arête frontière.
- À la fin, on enlève les triangles qui utilisent les sommets du super-triangle.

"""

from __future__ import annotations

from typing import List, Sequence, Tuple
import math

Point = Tuple[float, float]
Triangle = Tuple[int, int, int]


# ----------------- utilitaires géométriques -----------------


def _area2(a: Point, b: Point, c: Point) -> float:
    """Retourne 2 * aire orientée du triangle ABC."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _is_collinear(points: Sequence[Point], eps: float = 1e-9) -> bool:
    """True si tous les points sont (quasi) sur une même droite."""
    if len(points) < 3:
        return True
    a, b = points[0], points[1]
    for c in points[2:]:
        if abs(_area2(a, b, c)) > eps:
            return False
    return True


def _in_circumcircle(p: Point, a: Point, b: Point, c: Point) -> bool:
    """Retourne True si le point p est strictement à l'intérieur du cercle circonscrit à ABC.

    On utilise la formulation déterminant classique. On suppose ABC en orientation CCW
    (sinon le signe est inversé, cf. aire orientée).
    """
    # Recentrer par rapport à p pour limiter les grosses valeurs
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


def _build_super_triangle(points: Sequence[Point]) -> Tuple[Point, Point, Point]:
    """Construit un super-triangle englobant tous les points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    dx = max_x - min_x
    dy = max_y - min_y
    dmax = max(dx, dy) or 1.0  # éviter 0 si tous les points sont identiques
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0

    # Triangle très large
    p1 = (mid_x - 20 * dmax, mid_y - dmax)
    p2 = (mid_x, mid_y + 20 * dmax)
    p3 = (mid_x + 20 * dmax, mid_y - dmax)
    return p1, p2, p3


def delaunay_triangulation(points: Sequence[Point], eps: float = 1e-9) -> List[Triangle]:
    """Triangulation type Delaunay de points 2D.

    Retourne une liste de triangles, chaque triangle étant un triplet
    d'indices dans la liste `points` d'origine.
    """
    n = len(points)
    if n < 3:
        return []
    if _is_collinear(points, eps=eps):
        return []

    # Copie locale des points + super-triangle à la fin
    pts: List[Point] = list(points)
    st_a, st_b, st_c = _build_super_triangle(points)
    idx_a = len(pts)
    idx_b = idx_a + 1
    idx_c = idx_a + 2
    pts.extend([st_a, st_b, st_c])

    # Liste des triangles, exprimés en indices dans `pts`
    triangles: List[Triangle] = [(idx_a, idx_b, idx_c)]

    # Insertion incrémentale des points (0..n-1)
    for pi in range(n):
        p = pts[pi]

        bad_triangles: List[Triangle] = []
        for t in triangles:
            ia, ib, ic = t
            a, b, c = pts[ia], pts[ib], pts[ic]

            # Sauter triangles quasi dégénérés
            if abs(_area2(a, b, c)) < eps:
                continue

            # On veut ABC en orientation CCW pour la formule
            if _area2(a, b, c) < 0:
                # Permuter pour rendre CCW
                b, c = c, b
                ib, ic = ic, ib

            if _in_circumcircle(p, a, b, c):
                bad_triangles.append((ia, ib, ic))

        # Construire le "contour" du trou : arêtes uniques
        polygon_edges: List[Tuple[int, int]] = []

        def add_edge(e: Tuple[int, int]) -> None:
            """Ajoute une arête si absente, sinon la retire (arête interne)."""
            a, b = e
            edge = (a, b)
            rev = (b, a)
            if rev in polygon_edges:
                polygon_edges.remove(rev)
            elif edge in polygon_edges:
                polygon_edges.remove(edge)
            else:
                polygon_edges.append(edge)

        for ia, ib, ic in bad_triangles:
            add_edge((ia, ib))
            add_edge((ib, ic))
            add_edge((ic, ia))

        # On enlève les triangles "mauvais"
        for t in bad_triangles:
            if t in triangles:
                triangles.remove(t)

        # On crée de nouveaux triangles entre le point courant et chaque arête frontalière
        for (ia, ib) in polygon_edges:
            # On peut filtrer les triangles très petits plus tard
            triangles.append((ia, ib, pi))

    # On retire les triangles qui utilisent les sommets du super-triangle
    result: List[Triangle] = []
    for ia, ib, ic in triangles:
        if ia >= n or ib >= n or ic >= n:
            continue
        a, b, c = pts[ia], pts[ib], pts[ic]
        if abs(_area2(a, b, c)) <= eps:
            continue
        result.append((ia, ib, ic))

    return result


# Pour rester compatible avec les tests existants,
# on expose un nom triangulate_fan qui utilise en fait notre Delaunay.
def triangulate_fan(points: Sequence[Point], eps: float = 1e-9) -> List[Triangle]:
    """Compatibilité TP : alias vers la triangulation de type Delaunay.

    Les tests pourront évoluer pour vérifier uniquement :
    - pas de triangles si <3 points ou colinéarité
    - sinon, au moins un triangle et indices valides.
    """
    return delaunay_triangulation(points, eps=eps)
