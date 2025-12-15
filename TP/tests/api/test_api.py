"""Tests de l'API Flask du Triangulator."""
from unittest.mock import patch

from triangulator import binary
from triangulator.app import app
from werkzeug.exceptions import NotFound


def _client():
    """Retourne un client de test Flask."""
    app.testing = True
    return app.test_client()


# =============================================================================
# Tests Health Check
# =============================================================================

def test_healthz_ok():
    """Doit passer (ton stub renvoie déjà 'ok')."""
    c = _client()
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.data == b"ok"


def test_healthz_method_not_allowed():
    """Health check n'accepte que GET."""
    c = _client()
    r = c.post("/healthz")
    assert r.status_code == 405


# =============================================================================
# Tests Triangulate - Happy Path
# =============================================================================

def test_triangulate_happy_path_should_pass_now():
    """Mocke le PointSetManager pour forcer un happy-path.

    Doit PASSER maintenant que l'endpoint décode / triangule / encode.
    """
    pts = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    raw = binary.encode_pointset(pts)

    with patch("triangulator.client.fetch_pointset_binary", return_value=raw):
        c = _client()
        r = c.get("/triangulate/42")
        assert r.status_code == 200
        pts_out, tris_out = binary.decode_triangles(r.data)
        assert len(tris_out) == 1


def test_triangulate_simple_triangle():
    """Triangle simple - happy path complet."""
    pts = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    raw_in = binary.encode_pointset(pts)
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=raw_in
    ):
        c = _client()
        r = c.get("/triangulate/1")

        assert r.status_code == 200
        assert len(r.data) > 0
        pts_out, tris_out = binary.decode_triangles(r.data)
        assert len(pts_out) == 3
        assert len(tris_out) == 1


# =============================================================================
# Tests Triangulate - Erreurs Upstream
# =============================================================================

def test_triangulate_upstream_maps_502():
    """Doit passer: fetch lève -> on attend 502 JSON error."""
    def boom(*_, **__):
        raise RuntimeError("upstream down")

    with patch(
        "triangulator.client.fetch_pointset_binary", side_effect=boom
    ):
        c = _client()
        r = c.get("/triangulate/99")
    assert r.status_code == 502
    assert r.is_json and "code" in r.json


def test_triangulate_404_not_found():
    """Point set inexistant côté PointSetManager."""
    def not_found(*_, **__):
        raise NotFound()

    with patch(
        "triangulator.client.fetch_pointset_binary", side_effect=not_found
    ):
        c = _client()
        r = c.get("/triangulate/999999")
    assert r.status_code == 404
    assert r.is_json and "code" in r.json


def test_triangulate_upstream_timeout():
    """Timeout lors du fetch (si implémenté)."""
    def slow(*_, **__):
        raise TimeoutError("Request timeout")

    with patch(
        "triangulator.client.fetch_pointset_binary", side_effect=slow
    ):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code == 502


# =============================================================================
# Tests Triangulate - Données Corrompues
# =============================================================================

def test_triangulate_corrupt_data():
    """Données corrompues depuis upstream."""
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=b"garbage"
    ):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code == 422
    if r.is_json:
        assert "code" in r.json


def test_triangulate_empty_response():
    """Upstream renvoie une réponse vide."""
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=b""
    ):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code == 422


def test_triangulate_partial_data():
    """Buffer incomplet depuis upstream."""
    corrupt = b'\x0a\x00\x00\x00'
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=corrupt
    ):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code == 422


# =============================================================================
# Tests Triangulate - Cas Limites
# =============================================================================

def test_triangulate_collinear_returns_empty():
    """Points colinéaires -> 0 triangles -> réponse vide valide."""
    pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    raw = binary.encode_pointset(pts)
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=raw
    ):
        c = _client()
        r = c.get("/triangulate/1")
        assert r.status_code == 200
        pts_out, tris_out = binary.decode_triangles(r.data)
        assert len(tris_out) == 0


def test_triangulate_two_points():
    """Moins de 3 points -> 0 triangles."""
    pts = [(0.0, 0.0), (1.0, 0.0)]
    raw = binary.encode_pointset(pts)
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=raw
    ):
        c = _client()
        r = c.get("/triangulate/1")
        assert r.status_code == 200
        pts_out, tris_out = binary.decode_triangles(r.data)
        assert len(tris_out) == 0


def test_triangulate_large_pointset():
    """Grand ensemble de points."""
    pts = [(float(i % 50), float(i // 50)) for i in range(500)]
    raw = binary.encode_pointset(pts)
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=raw
    ):
        c = _client()
        r = c.get("/triangulate/1")
        assert r.status_code == 200
        pts_out, tris_out = binary.decode_triangles(r.data)
        assert len(tris_out) == 882


# =============================================================================
# Tests Triangulate - Validation des Entrées
# =============================================================================

def test_triangulate_invalid_id_negative():
    """ID négatif doit être rejeté."""
    c = _client()
    r = c.get("/triangulate/-1")
    assert r.status_code == 502


def test_triangulate_invalid_id_zero():
    """ID=0 pourrait être invalide selon design."""
    c = _client()
    r = c.get("/triangulate/0")
    assert r.status_code in (502, 404)


def test_triangulate_invalid_id_string():
    """ID non-numérique."""
    c = _client()
    r = c.get("/triangulate/abc")
    assert r.status_code == 502


def test_triangulate_invalid_id_float():
    """ID flottant."""
    c = _client()
    r = c.get("/triangulate/3.14")
    assert r.status_code == 502


# =============================================================================
# Tests Triangulate - Méthodes HTTP
# =============================================================================

def test_triangulate_method_not_allowed():
    """Doit passer si Flask répond 405 aux méthodes non-GET."""
    c = _client()
    r = c.post("/triangulate/1")
    assert r.status_code == 405


def test_triangulate_put_not_allowed():
    """PUT non autorisé."""
    c = _client()
    r = c.put("/triangulate/1")
    assert r.status_code == 405


def test_triangulate_delete_not_allowed():
    """DELETE non autorisé."""
    c = _client()
    r = c.delete("/triangulate/1")
    assert r.status_code == 405


# =============================================================================
# Tests Triangulate - Headers et Content-Type
# =============================================================================

def test_triangulate_response_content_type():
    """Vérifier que la réponse est bien application/octet-stream."""
    pts = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    raw = binary.encode_pointset(pts)
    with patch(
        "triangulator.client.fetch_pointset_binary", return_value=raw
    ):
        c = _client()
        r = c.get("/triangulate/1")
        assert r.status_code == 200
        assert r.content_type == "application/octet-stream"


def test_triangulate_error_is_json():
    """Les erreurs doivent être en JSON."""
    def boom(*_, **__):
        raise RuntimeError("test error")

    with patch(
        "triangulator.client.fetch_pointset_binary", side_effect=boom
    ):
        c = _client()
        r = c.get("/triangulate/1")

    if r.status_code >= 400:
        assert r.is_json
        assert "code" in r.json


# =============================================================================
# Tests Routes Inexistantes
# =============================================================================

def test_route_not_found():
    """Route qui n'existe pas."""
    c = _client()
    r = c.get("/nonexistent")
    assert r.status_code == 404


def test_triangulate_without_id():
    """Endpoint sans ID."""
    c = _client()
    r = c.get("/triangulate/")
    assert r.status_code in (404, 308)


def test_root_route():
    """Route racine."""
    c = _client()
    r = c.get("/")
    assert r.status_code in (404, 200)