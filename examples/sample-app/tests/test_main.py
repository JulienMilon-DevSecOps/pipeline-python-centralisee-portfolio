"""Tests de l'API d'exemple (exécutés par le job pytest de la CI de la vitrine)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    """La route /health répond 200 avec le statut "ok"."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version() -> None:
    """La route /version renvoie la version du package installé."""
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0"}
