"""Tests unitaires pour l'algorithme de triangulation."""
from triangulator import algo


def test_less_than_three_points():
    """Doit passer avec le stub actuel (renvoie [])."""
    assert algo.triangulate_fan([]) == []
    assert algo.triangulate_fan([(0, 0), (1, 1)]) == []


def test_three_points_one_triangle():
    """Doit échouer tant que l'algo renvoie [] pour n>=3."""
    pts = [(0, 0), (1, 0), (0, 1)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 1
    a, b, c = tris[0]
    assert {a, b, c} == {0, 1, 2}


def test_all_collinear_zero_triangle():
    """Peut échouer ou passer selon si tu traites déjà la colinéarité."""
    pts = [(0, 0), (1, 0), (2, 0), (3, 0)]
    tris = algo.triangulate_fan(pts)
    assert tris == []


def test_convex_five_points_n_minus_2():
    """Doit échouer tant que l'algo est stub."""
    pts = [(0, 0), (2, 0), (3, 1), (2, 2), (0, 2)]  # convexe
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 3  # n-2


def test_duplicate_points():
    """Points dupliqués doivent être gérés (erreur ou filtrage)."""
    pts = [(0, 0), (1, 0), (1, 0), (0, 1)]  # point dupliqué
    # Comportement à définir : lever ValueError ou filtrer
    # Pour l'instant on teste qu'il ne plante pas
    tris = algo.triangulate_fan(pts)
    # Si filtrage : len(tris) == 1
    # Si erreur : ValueError levée
    assert isinstance(tris, list)


def test_negative_coordinates():
    """Coordonnées négatives doivent fonctionner."""
    pts = [(-1, -1), (1, -1), (0, 1)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 1


def test_large_coordinates():
    """Très grandes valeurs doivent être supportées."""
    pts = [(0, 0), (1e6, 0), (0, 1e6)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 1


def test_concave_polygon():
    """Polygone concave - l'algo fan peut ne pas gérer correctement."""
    # En forme de flèche : <>
    pts = [(0, 1), (1, 0), (2, 1), (1, 0.5)]
    tris = algo.triangulate_fan(pts)
    # Fan triangulation peut produire des triangles qui se chevauchent
    # On vérifie juste qu'il produit n-2 triangles
    assert len(tris) == 2  # n-2 = 4-2


def test_points_not_in_order():
    """Points en désordre (non triés angulairement)."""
    pts = [(0, 0), (0, 1), (1, 0), (1, 1)]  # carré
    tris = algo.triangulate_fan(pts)
    # L'algo fan nécessite un ordre spécifique
    # On vérifie qu'il produit le bon nombre de triangles
    assert len(tris) == 2  # n-2


def test_very_small_triangle():
    """Triangle avec aire quasi-nulle (problème numérique)."""
    pts = [(0, 0), (1e-10, 0), (0, 1e-10)]
    tris = algo.triangulate_fan(pts)
    # Doit-il être rejeté ou accepté ?
    # On teste qu'il ne plante pas
    assert isinstance(tris, list)


def test_square_four_points():
    """Carré simple - cas classique."""
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 2  # n-2 = 4-2


def test_many_points():
    """Test avec 10 points pour vérifier la formule n-2."""
    pts = [(float(i), float(i % 3)) for i in range(10)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 8  # n-2 = 10-2


def test_triangle_indices_valid():
    """Vérifier que les indices des triangles sont valides."""
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tris = algo.triangulate_fan(pts)
    n = len(pts)
    for tri in tris:
        assert len(tri) == 3
        for idx in tri:
            assert 0 <= idx < n


def test_mixed_coordinates():
    """Mélange de coordonnées positives et négatives."""
    pts = [(-5, -5), (5, -5), (5, 5), (-5, 5), (0, 0)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 3  # n-2 = 5-2


def test_float_precision():
    """Points avec haute précision décimale."""
    pts = [(0.123456789, 0.987654321), (1.111111111, 0.222222222), (0.333333333, 1.444444444)]
    tris = algo.triangulate_fan(pts)
    assert len(tris) == 1