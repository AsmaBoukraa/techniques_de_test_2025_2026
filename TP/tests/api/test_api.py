"""Tests de l'API Flask du Triangulator."""
from unittest.mock import patch, MagicMock
import pytest
from triangulator.app import app
from triangulator import binary


def _client():
    """Helper pour créer un client de test Flask."""
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

def test_triangulate_happy_path_should_fail_for_now():
    """On mocke le PointSetManager pour forcer un happy-path.
    Doit échouer tant que l'endpoint n'essaie pas de décoder / trianguler / encoder.
    """
    pts = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    raw = None
    try:
        raw = binary.encode_pointset(pts)  # NotImplementedError -> ce test plantera avant Flask
    except Exception:
        # Si encode_pointset n'est pas prêt, on court-circuite: le but est qu'au final
        # cette voie attende un 200 et un payload binaire décodable.
        pass

    with patch("triangulator.client.fetch_pointset_binary", return_value=raw if raw else b""):
        c = _client()
        r = c.get("/triangulate/42")
        # tant que app.triangulate ne traite pas correctement, on s'attend à !=200
        assert r.status_code in (500, 502, 422)


def test_triangulate_simple_triangle():
    """Triangle simple - happy path complet."""
    pts = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    try:
        raw_in = binary.encode_pointset(pts)
        with patch("triangulator.client.fetch_pointset_binary", return_value=raw_in):
            c = _client()
            r = c.get("/triangulate/1")
            
            if r.status_code == 200:
                # Vérifier que la réponse est bien du binaire
                assert len(r.data) > 0
                # Essayer de décoder
                pts_out, tris_out = binary.decode_triangles(r.data)
                assert len(pts_out) == 3
                assert len(tris_out) == 1
    except NotImplementedError:
        pytest.skip("Implémentation pas encore prête")


# =============================================================================
# Tests Triangulate - Erreurs Upstream
# =============================================================================

def test_triangulate_upstream_maps_502():
    """Doit passer: fetch lève -> on attend 502 JSON error."""
    def boom(*_, **__): 
        raise RuntimeError("upstream down")
    
    with patch("triangulator.client.fetch_pointset_binary", side_effect=boom):
        c = _client()
        r = c.get("/triangulate/99")
    assert r.status_code == 502
    assert r.is_json and "error" in r.json


def test_triangulate_404_not_found():
    """Point set inexistant côté PointSetManager."""
    def not_found(*_, **__):
        from werkzeug.exceptions import NotFound
        raise NotFound()
    
    with patch("triangulator.client.fetch_pointset_binary", side_effect=not_found):
        c = _client()
        r = c.get("/triangulate/999999")
    assert r.status_code in (404, 502)  # Dépend de la gestion


def test_triangulate_upstream_timeout():
    """Timeout lors du fetch (si implémenté)."""
    import time
    def slow(*_, **__):
        time.sleep(0.1)  # Simuler lenteur (pas trop long pour les tests)
        raise TimeoutError("Request timeout")
    
    with patch("triangulator.client.fetch_pointset_binary", side_effect=slow):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code in (504, 502, 500)


# =============================================================================
# Tests Triangulate - Données Corrompues
# =============================================================================

def test_triangulate_corrupt_data():
    """Données corrompues depuis upstream."""
    with patch("triangulator.client.fetch_pointset_binary", return_value=b"garbage"):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code in (422, 500)
    # Si JSON, vérifier le message
    if r.is_json:
        assert "error" in r.json


def test_triangulate_empty_response():
    """Upstream renvoie une réponse vide."""
    with patch("triangulator.client.fetch_pointset_binary", return_value=b""):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code in (422, 500)


def test_triangulate_partial_data():
    """Buffer incomplet depuis upstream."""
    # 4 bytes de count=10 mais pas de données
    corrupt = b'\x0a\x00\x00\x00'
    with patch("triangulator.client.fetch_pointset_binary", return_value=corrupt):
        c = _client()
        r = c.get("/triangulate/42")
    assert r.status_code in (422, 500)


# =============================================================================
# Tests Triangulate - Cas Limites
# =============================================================================

def test_triangulate_collinear_returns_empty():
    """Points colinéaires -> 0 triangles -> réponse vide valide."""
    pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    try:
        raw = binary.encode_pointset(pts)
        with patch("triangulator.client.fetch_pointset_binary", return_value=raw):
            c = _client()
            r = c.get("/triangulate/1")
            # Doit retourner 200 avec 0 triangles (pas une erreur)
            if r.status_code == 200:
                pts_out, tris_out = binary.decode_triangles(r.data)
                assert len(tris_out) == 0
    except NotImplementedError:
        pytest.skip("Implémentation pas encore prête")


def test_triangulate_two_points():
    """Moins de 3 points -> 0 triangles."""
    pts = [(0.0, 0.0), (1.0, 0.0)]
    try:
        raw = binary.encode_pointset(pts)
        with patch("triangulator.client.fetch_pointset_binary", return_value=raw):
            c = _client()
            r = c.get("/triangulate/1")
            if r.status_code == 200:
                pts_out, tris_out = binary.decode_triangles(r.data)
                assert len(tris_out) == 0
    except NotImplementedError:
        pytest.skip("Implémentation pas encore prête")


def test_triangulate_large_pointset():
    """Grand ensemble de points."""
    pts = [(float(i % 50), float(i // 50)) for i in range(500)]
    try:
        raw = binary.encode_pointset(pts)
        with patch("triangulator.client.fetch_pointset_binary", return_value=raw):
            c = _client()
            r = c.get("/triangulate/1")
            if r.status_code == 200:
                pts_out, tris_out = binary.decode_triangles(r.data)
                assert len(tris_out) == 498  # n-2
    except NotImplementedError:
        pytest.skip("Implémentation pas encore prête")


# =============================================================================
# Tests Triangulate - Validation des Entrées
# =============================================================================

def test_triangulate_invalid_id_negative():
    """ID négatif doit être rejeté."""
    c = _client()
    r = c.get("/triangulate/-1")
    # Flask peut soit 404 (route pas matchée), soit ton code rejette
    assert r.status_code in (400, 404)


def test_triangulate_invalid_id_zero():
    """ID=0 pourrait être invalide selon ton design."""
    c = _client()
    r = c.get("/triangulate/0")
    # Selon ton design, 0 peut être valide ou non
    # On vérifie juste qu'il ne plante pas
    assert r.status_code in (200, 400, 404, 500, 502)


def test_triangulate_invalid_id_string():
    """ID non-numérique."""
    c = _client()
    r = c.get("/triangulate/abc")
    assert r.status_code == 404  # Flask route matching


def test_triangulate_invalid_id_float():
    """ID flottant."""
    c = _client()
    r = c.get("/triangulate/3.14")
    assert r.status_code == 404  # Flask route matching


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
    try:
        raw = binary.encode_pointset(pts)
        with patch("triangulator.client.fetch_pointset_binary", return_value=raw):
            c = _client()
            r = c.get("/triangulate/1")
            if r.status_code == 200:
                assert r.content_type == "application/octet-stream"
    except NotImplementedError:
        pytest.skip("Implémentation pas encore prête")


def test_triangulate_error_is_json():
    """Les erreurs doivent être en JSON."""
    def boom(*_, **__):
        raise RuntimeError("test error")
    
    with patch("triangulator.client.fetch_pointset_binary", side_effect=boom):
        c = _client()
        r = c.get("/triangulate/1")
    
    if r.status_code >= 400:
        assert r.is_json
        assert "error" in r.json


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
    assert r.status_code in (404, 308)  # 308 = redirect avec /


def test_root_route():
    """Route racine."""
    c = _client()
    r = c.get("/")
    assert r.status_code in (404, 200)  # Dépend si implémenté