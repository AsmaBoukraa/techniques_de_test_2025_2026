import time
import pytest
from triangulator import algo, binary

pytestmark = pytest.mark.perf


def test_triangulation_100_points():
    pts = [(float(i), float(i**0.5)) for i in range(100)]
    start = time.perf_counter()

    tris = algo.triangulate_fan(pts)

    duration = time.perf_counter() - start
    assert duration < 1.0


def test_encode_pointset_10000_points():
    pts = [(float(i), -float(i)) for i in range(10000)]
    start = time.perf_counter()

    buf = binary.encode_pointset(pts)

    duration = time.perf_counter() - start
    assert duration < 1.0
    assert len(buf) == 4 + 10000 * 8


def test_full_pipeline_perf():
    pts = [(float(i % 50), float(i // 50)) for i in range(500)]

    start = time.perf_counter()

    raw = binary.encode_pointset(pts)
    decoded = binary.decode_pointset(raw)
    tris = algo.triangulate_fan(decoded)
    raw2 = binary.encode_triangles(decoded, tris)

    duration = time.perf_counter() - start

    assert duration < 3.0
    assert len(raw2) > 0
