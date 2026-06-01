# core/health.py
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Lightweight health check used by Railway's deployment pipeline.
    Returns 200 if Django is running and the database is reachable.
    """
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
    }, status=200 if db_ok else 503)
