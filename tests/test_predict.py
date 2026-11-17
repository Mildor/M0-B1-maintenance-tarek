"""Tests fonctionnels de l'endpoint /predict.
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_cas_valide():
    """L'endpoint /predict doit répondre 200 OK avec le bon payload chargé"""
    with TestClient(app) as client:
        payload = {
            "type_machine": "compresseur",
            "age_machine_jours": 2000,
            "derniere_maintenance_jours": 39,
            "temperature_moyenne": 34.5,
            "vibration_moyenne": 2.87,
            "pression_moyenne": 6.3,
            "nb_incidents_3_mois": 4
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body['criticite'] in {"basse", "moyenne", "haute"}
        assert body['probabilites'].keys() == {"basse", "moyenne", "haute"}
        assert sum(body['probabilites'].values()) == pytest.approx(1.0)


def test_machine_invalide():
    """L'endpoint /predict doit répondre 422"""
    with TestClient(app) as client:
        payload = {
            "type_machine": "FAUSEEMACHINE",
            "age_machine_jours": 2000,
            "derniere_maintenance_jours": 39,
            "temperature_moyenne": 34.5,
            "vibration_moyenne": 2.87,
            "pression_moyenne": 6.3,
            "nb_incidents_3_mois": 4
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 422


@pytest.mark.parametrize("type_m", ["pompe", "compresseur", "convoyeur", "presse", "four"])
def test_cas_valide_all_machine(type_m):
    """L'endpoint /predict doit répondre 200 OK avec les 5 machines"""
    with TestClient(app) as client:
        payload = {
            "type_machine": type_m,
            "age_machine_jours": 2000,
            "derniere_maintenance_jours": 39,
            "temperature_moyenne": 34.5,
            "vibration_moyenne": 2.87,
            "pression_moyenne": 6.3,
            "nb_incidents_3_mois": 4
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body['criticite'] in {"basse", "moyenne", "haute"}
        assert body['probabilites'].keys() == {"basse", "moyenne", "haute"}
        assert sum(body['probabilites'].values()) == pytest.approx(1.0)
