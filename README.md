# FastIA — API de maintenance prédictive (criticité machine)

Service REST FastAPI exposant un modèle scikit-learn pré-entraîné pour classifier la criticité d'incidents machine en 3 niveaux (`basse`, `moyenne`, `haute`) à partir de 7 caractéristiques observables.

---

## Architecture

### Vue d'ensemble

- **API (`app/main.py`)** : application FastAPI (`v0.1.0`) utilisant un gestionnaire `lifespan` pour charger le modèle `model/model.joblib` une seule fois au démarrage en mémoire (`state["model"]`), puis le libérer à l'arrêt.
- **Validation (`app/schemas.py`)** : schémas Pydantic v2 (`MachineInput`, `PredictionResponse`, `HealthResponse`) garantissant les types, les valeurs autorisées (`type_machine` parmi `pompe`, `compresseur`, `convoyeur`, `presse`, `four`) et les bornes métier.
- **Modèle (`model/model.joblib`)** : pipeline scikit-learn (`ColumnTransformer` avec `StandardScaler` + `OneHotEncoder`, suivi d'un `RandomForestClassifier`), entraîné sur `data/maintenance_data.csv` via `model/train_baseline.py`.
- **Journalisation** : assurée par **Loguru** avec écriture dans `logs/api.log` (rotation à `40 MB`, rétention `7 days`, compression `zip`), traçant les entrées, les sorties et la durée d'exécution de chaque prédiction.

### Structure du projet

```text
M0-B1-maintenance-tarek/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application FastAPI, lifespan, routes /health et /predict, logs Loguru
│   └── schemas.py           # Schémas Pydantic (MachineInput, PredictionResponse, HealthResponse)
├── data/
│   ├── generate_dataset.py  # Script de génération du dataset synthétique
│   └── maintenance_data.csv # Dataset d'entraînement
├── model/
│   ├── train_baseline.py    # Script d'entraînement du pipeline scikit-learn
│   └── model.joblib         # Modèle sérialisé chargé au démarrage
├── tests/
│   ├── __init__.py
│   ├── test_health.py       # Tests de l'endpoint GET /health
│   └── test_predict.py      # Tests de l'endpoint POST /predict (valide, 422, 5 types de machine)
├── logs/
│   └── api.log              # Fichier de logs généré par Loguru
├── Dockerfile               # Image Docker Python 3.11-slim + uv + HEALTHCHECK
└── requirements.txt         # Dépendances Python figées
```

### Endpoints

| Méthode | Route      | Description                                          | Réponse                                       |
| ------- | ---------- | ---------------------------------------------------- | --------------------------------------------- |
| `GET`   | `/health`  | Vérifie l'état du service et le chargement du modèle | `{"status": "ok", "model_loaded": true}`      |
| `POST`  | `/predict` | Prédit la criticité et les probabilités par classe   | `{"criticite": "...", "probabilites": {...}}` |
| `GET`   | `/docs`    | Documentation interactive Swagger UI                 | Interface OpenAPI                             |

---

## Comment lancer le service

### 1. En local (Python)

Prérequis : Python 3.11+

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
uvicorn app.main:app --reload
```

L'API est accessible sur `http://localhost:8000` et la documentation Swagger sur `http://localhost:8000/docs`.

### 2. Avec Docker

Le `Dockerfile` utilise `python:3.11-slim`, installe les dépendances via `uv`, expose le port `8000` et intègre un `HEALTHCHECK` sur `/health`.

```bash
# Construire l'image
docker build -t fastia-maintenance:dev .

# Lancer le conteneur
docker run -d -p 8000:8000 --name fastia-maintenance:dev fastia-maintenance:dev
```

## Comment tester

La suite de tests utilise **pytest** et le `TestClient` de FastAPI :

```bash
# Avec l'environnement virtuel activé
pytest -v
```

## Preuves

### Pytest

```text
(M0-B1-maintenance-tarek) tarek@DESKTOP-QO2LOTN:~/formation/M0-B1-maintenance-tarek$ pytest -v

=== test session starts ===
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.7.0 -- /home/tarek/formation/M0-B1-maintenance-tarek/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/tarek/formation/M0-B1-maintenance-tarek
plugins: Faker-40.52.0, anyio-4.6.2.post1
collected 9 items

tests/test_health.py::test_health_returns_200 PASSED                                                                                                                                                                                                                                                                                  [ 11%]
tests/test_health.py::test_health_response_schema PASSED                                                                                                                                                                                                                                                                              [ 22%]
tests/test_predict.py::test_cas_valide PASSED                                                                                                                                                                                                                                                                                         [ 33%]
tests/test_predict.py::test_machine_invalide PASSED                                                                                                                                                                                                                                                                                   [ 44%]
tests/test_predict.py::test_cas_valide_all_machine[pompe] PASSED                                                                                                                                                                                                                                                                      [ 55%]
tests/test_predict.py::test_cas_valide_all_machine[compresseur] PASSED                                                                                                                                                                                                                                                                [ 66%]
tests/test_predict.py::test_cas_valide_all_machine[convoyeur] PASSED                                                                                                                                                                                                                                                                  [ 77%]
tests/test_predict.py::test_cas_valide_all_machine[presse] PASSED                                                                                                                                                                                                                                                                     [ 88%]
tests/test_predict.py::test_cas_valide_all_machine[four] PASSED                                                                                                                                                                                                                                                                       [100%]

===9 passed in 2.88s ===
```

### Réponse curl /health

```text
(M0-B1-maintenance-tarek) tarek@DESKTOP-QO2LOTN:~/formation/M0-B1-maintenance-tarek$ sudo docker ps
CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS                    PORTS                                         NAMES
5b94f7876159   fastia-maintenance:dev   "uvicorn app.main:ap…"   13 minutes ago   Up 13 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp   distracted_dijkstra
(M0-B1-maintenance-tarek) tarek@DESKTOP-QO2LOTN:~/formation/M0-B1-maintenance-tarek$ curl http://localhost:8000/health
{"status":"ok","model_loaded":true}
```

### Docker images

```text
(M0-B1-maintenance-tarek) tarek@DESKTOP-QO2LOTN:~/formation/M0-B1-maintenance-tarek$ sudo docker images

IMAGE                    ID             DISK USAGE   CONTENT SIZE   EXTRA
fastia-maintenance:dev   e7d1d136d2ad        664MB          156MB    U
hello-world:latest       1e4c05b897a7       25.9kB         9.49kB
python:3.12-slim         5e2bdb1b0d54        180MB         45.5MB
```
