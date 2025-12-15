"""Codec pour l'encodage et le décodage binaire des PointSet et Triangles."""
import math
import struct
from typing import List, Sequence, Tuple


# Définition directe pour éviter les imports circulaires
class BinaryCodecError(Exception):
    """Exception pour les erreurs de codage binaire."""

Point = Tuple[float, float]
Triangle = Tuple[int, int, int]
_FLOAT_FORMAT = "<f"
_ULONG_FORMAT = "<I"
_POINT_FORMAT = "<ff"
_TRIANGLE_FORMAT = "<III"
_COUNT_SIZE = 4  # size of unsigned long (I)


def encode_pointset(points: Sequence[Point]) -> bytes:
    """Encode une séquence de points en représentation binaire.

    Format: count (4 bytes ULong) + points (N * 8 bytes, X: float, Y: float).
    """
    n = len(points)

    # 1. Validation des NaN/Inf (requis par les tests unitaires)
    for x, y in points:
        if math.isnan(x) or math.isinf(x) or math.isnan(y) or math.isinf(y):
            raise ValueError("Point coordinates must be finite real numbers.")

    # 2. Emballage du nombre de points
    buffer = struct.pack(_ULONG_FORMAT, n)

    # 3. Emballage des points (X, Y)
    for x, y in points:
        buffer += struct.pack(_POINT_FORMAT, x, y)

    return buffer


def decode_pointset(buf: bytes) -> List[Point]:
    """Décode la représentation binaire PointSet en liste de points Python."""
    if len(buf) < _COUNT_SIZE:
        raise BinaryCodecError("Buffer is too short to contain point count.")

    # 1. Déballage du nombre de points
    n = struct.unpack(_ULONG_FORMAT, buf[:_COUNT_SIZE])[0]

    expected_size = _COUNT_SIZE + n * 8
    if len(buf) != expected_size:
        raise BinaryCodecError(
            f"Buffer size {len(buf)} does not match expected size "
            f"{expected_size} for {n} points."
        )

    points = []
    offset = _COUNT_SIZE
    for _ in range(n):
        x, y = struct.unpack(_POINT_FORMAT, buf[offset:offset + 8])
        points.append((x, y))
        offset += 8

    return points


def encode_triangles(
    points: Sequence[Point], tris: Sequence[Triangle]
) -> bytes:
    """Encode les points et les triangles en binaire.

    Format: PointSet binaire + T_count (4 bytes ULong) +
    triangles (T * 12 bytes, 3 indices: ULong).
    """
    # 1. Validation des indices de triangles (requis par les tests unitaires)
    n_points = len(points)

    for tri in tris:
        if len(tri) != 3:
            raise BinaryCodecError(
                f"Triangle tuple must have exactly 3 indices, found {len(tri)}."
            )

        for idx in tri:
            # Vérifie l'indice
            if not isinstance(idx, int) or idx < 0 or idx >= n_points:
                raise ValueError(
                    f"Triangle index {idx} is out of bounds [0, {n_points - 1}] "
                    f"or not an integer."
                )

    # 2. Partie Vertices (PointSet)
    buffer = encode_pointset(points)

    # 3. Partie Triangles (count)
    n_tris = len(tris)
    buffer += struct.pack(_ULONG_FORMAT, n_tris)

    # 4. Emballage des indices (idx1, idx2, idx3)
    for idx1, idx2, idx3 in tris:
        buffer += struct.pack(_TRIANGLE_FORMAT, idx1, idx2, idx3)

    return buffer


def decode_triangles(buf: bytes) -> Tuple[List[Point], List[Triangle]]:
    """Décode le binaire Triangles en liste de points et liste de triangles."""
    if len(buf) < _COUNT_SIZE:
        raise BinaryCodecError("Buffer is too short to contain point count.")

    # 1. Décodage de la partie PointSet (Vertices)
    n_points = struct.unpack(_ULONG_FORMAT, buf[:_COUNT_SIZE])[0]
    pointset_size = _COUNT_SIZE + n_points * 8

    if len(buf) < pointset_size + _COUNT_SIZE:
        raise BinaryCodecError(
            "Buffer is too short to contain PointSet and triangle count."
        )

    # Décodage des points (on réutilise decode_pointset)
    points = decode_pointset(buf[:pointset_size])

    # 2. Décodage de la partie Triangles (count)
    offset = pointset_size
    n_tris = struct.unpack(
        _ULONG_FORMAT, buf[offset:offset + _COUNT_SIZE]
    )[0]

    # Vérification de la taille totale du buffer
    expected_size = pointset_size + _COUNT_SIZE + n_tris * 12
    if len(buf) != expected_size:
        raise BinaryCodecError(
            f"Buffer size {len(buf)} does not match expected size "
            f"{expected_size} for {n_tris} triangles."
        )

    offset += _COUNT_SIZE
    tris = []
    for _ in range(n_tris):
        idx1, idx2, idx3 = struct.unpack(
            _TRIANGLE_FORMAT, buf[offset:offset + 12]
        )
        tris.append((idx1, idx2, idx3))
        offset += 12

    return points, tris