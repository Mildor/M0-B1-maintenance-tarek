"""Tests fonctionnels de l'endpoint /predict.
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
import httpx

SAMPLE_PAYLOAD = {
    "type_machine": "compresseur",
    "age_machine_jours": 1500,
    "derniere_maintenance_jours": 45,
    "temperature_moyenne": 68.5,
    "vibration_moyenne": 3.2,
    "pression_moyenne": 7.8,
    "nb_incidents_3_mois": 2,
}

def test_explain_ollama_down_resturns_503_and_predict_workds():
    with TestClient(app) as client:
        with patch("app.main.httpx.post", side_effect=httpx.ConnectError("Connection refused")):
            res_explain = client.post("/explain", json=SAMPLE_PAYLOAD)
            assert res_explain.status_code == 503
        res_predict = client.post("/predict", json=SAMPLE_PAYLOAD)
        assert res_predict.status_code == 200
        data = res_predict.json()
        assert "criticite" in data
        assert "probabilites" in data
