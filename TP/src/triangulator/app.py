"""Contrôleur API Flask pour le micro-service Triangulator.

Gère le workflow complet (Fetch -> Decode -> Algo -> Encode) et les erreurs.
"""
import traceback

from flask import Flask, Response, jsonify
from werkzeug.exceptions import NotFound

# Imports absolus pour éviter l'erreur "ImportError: cannot import name 'app'"
from triangulator import algo, binary, client

app = Flask(__name__)


# Helper pour uniformiser les réponses d'erreurs en JSON
def _error_response(code: int, internal_code: str, message: str) -> Response:
    """Retourne une réponse JSON formatée avec le code HTTP approprié."""
    return jsonify({
        "code": internal_code,
        "message": message
    }), code


@app.get("/healthz")
def healthz():
    """Vérifie l'état de santé du service."""
    return "ok"


@app.get("/triangulate/<string:point_set_id>")
def triangulate(point_set_id: str):
    """Retourne la triangulation d'un ensemble de points donné par ID.

    Gère le workflow complet (Fetch -> Decode -> Algo -> Encode).
    """
    try:
        # 1. Fetch data from PointSetManager
        raw_data = client.fetch_pointset_binary(point_set_id)

        # 2. Decode PointSet
        try:
            points = binary.decode_pointset(raw_data)
        except Exception as e:
            return _error_response(
                422,
                "INVALID_POINTSET_DATA",
                f"Cannot decode PointSet binary data from upstream: {e}"
            )

        # 3. Compute triangulation
        try:
            triangles = algo.delaunay_triangulation(points)
        except Exception as e:
            print(f"Triangulation failed: {e}\n{traceback.format_exc()}")
            return _error_response(
                500,
                "TRIANGULATION_FAILED",
                "Triangulation could not be computed for the given point set."
            )

        # 4. Encode Triangles (Points + Triangles)
        try:
            raw_triangles = binary.encode_triangles(points, triangles)
        except Exception as e:
            print(f"Encoding failed: {e}\n{traceback.format_exc()}")
            return _error_response(
                500,
                "ENCODING_FAILED",
                "Failed to encode triangulation result."
            )

        # 5. Return response (200 OK)
        return Response(
            response=raw_triangles,
            status=200,
            mimetype="application/octet-stream"
        )

    except NotFound:
        return _error_response(
            404,
            "POINTSET_NOT_FOUND",
            f"The PointSet with ID '{point_set_id}' was not found "
            "(reported by PointSetManager)."
        )
    except (RuntimeError, TimeoutError) as e:
        return _error_response(
            502,
            "UPSTREAM_UNAVAILABLE",
            f"Communication with PointSetManager failed: {type(e).__name__}-{e}"
        )