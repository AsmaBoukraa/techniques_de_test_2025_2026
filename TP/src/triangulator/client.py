"""Stub pour le client HTTP vers PointSetManager (mock dans les tests API)."""


def fetch_pointset_binary(point_set_id: int) -> bytes:
    """Retourne une simulation du PointSet binaire (service amont)."""
    raise RuntimeError("Upstream not available (stub)")