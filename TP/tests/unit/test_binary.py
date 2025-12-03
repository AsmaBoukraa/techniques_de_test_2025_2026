import pytest
import math
from TP.src.triangulator import binary


def test_pointset_roundtrip_minimal():
    """Encode / decode basique."""
    pts = [(0.0, 0.0), (1.5, -2.25)]
    buf = binary.encode_pointset(pts)
    back = binary.decode_pointset(buf)
    assert back == pts


def test_pointset_empty():
    """Ensemble vide."""
    pts = []
    buf = binary.encode_pointset(pts)
    back = binary.decode_pointset(buf)
    assert back == []


def test_pointset_single_point():
    """Un seul point."""
    pts = [(3.14, 2.71)]
    buf = binary.encode_pointset(pts)
    back = binary.decode_pointset(buf)
    assert len(back) == 1


def test_pointset_large_dataset():
    """1000 points."""
    pts = [(float(i), float(i * 2)) for i in range(1000)]
    buf = binary.encode_pointset(pts)
    back = binary.decode_pointset(buf)
    assert len(back) == 1000


def test_pointset_reject_nan_inf_on_encode():
    """NaN / Inf doivent être refusés."""
    with pytest.raises(ValueError):
        binary.encode_pointset([(math.nan, 1)])

    with pytest.raises(ValueError):
        binary.encode_pointset([(math.inf, 0)])


def test_pointset_decode_wrong_size():
    """Taille incohérente."""
    buf = b"\x02\x00\x00\x00" + b"\x00" * 8  # 2 points annoncés mais 1 fourni
    with pytest.raises(Exception):
        binary.decode_pointset(buf)


def test_triangles_roundtrip_minimal():
    """Encode / decode triangles."""
    pts = [(0, 0), (1, 0), (0, 1)]
    tris = [(0, 1, 2)]
    buf = binary.encode_triangles(pts, tris)

    pts2, tris2 = binary.decode_triangles(buf)
    assert tris2 == tris


def test_triangles_multiple():
    """Plusieurs triangles."""
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    tris = [(0, 1, 2), (0, 2, 3)]
    buf = binary.encode_triangles(pts, tris)

    _, tris2 = binary.decode_triangles(buf)
    assert len(tris2) == 2


def test_triangles_index_oob_raises():
    """Index hors bornes."""
    pts = [(0, 0), (1, 0), (0, 1)]
    with pytest.raises(ValueError):
        binary.encode_triangles(pts, [(0, 1, 3)])


def test_triangles_negative_index():
    """Index négatif."""
    pts = [(0, 0), (1, 0), (0, 1)]
    with pytest.raises(ValueError):
        binary.encode_triangles(pts, [(0, -1, 2)])


def test_triangles_wrong_tuple_size():
    """Triangle invalide (≠3 indices)."""
    pts = [(0, 0), (1, 0), (0, 1)]
    with pytest.raises(Exception):
        binary.encode_triangles(pts, [(0, 1)])
