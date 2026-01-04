import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from backend.main import app
from backend.database import get_session
from backend.models import SeriesType

# Setup in-memory DB for integration tests
sqlite_file_name = "database_test.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

@pytest.fixture(name="client")
def client_fixture():
    create_db_and_tables()
    yield TestClient(app)
    SQLModel.metadata.drop_all(engine)

def test_full_curve_flow(client):
    # 1. Create Pump
    response = client.post("/pumps/", json={"manufacturer": "TestPump", "model": "ModelX"})
    assert response.status_code == 200
    pump_id = response.json()["id"]

    # 2. Create Curve Set
    response = client.post("/curve-sets/", json={"name": "Set1", "pump_id": pump_id, "units": {"flow": "gpm", "head": "ft"}})
    assert response.status_code == 200
    cs_id = response.json()["id"]

    # 3. Validate Points (Endpoint)
    points = [{"flow": 0, "value": 0}, {"flow": 50, "value": 50}, {"flow": 100, "value": 100}]
    response = client.post("/curve-sets/validate", json={"curve_type": "head", "points": points})
    assert response.status_code == 200
    data = response.json()
    assert not data["blocking_errors"]
    assert len(data["normalized_points"]) == 3

    # 4. Add Series (which fits)
    response = client.post(f"/curve-sets/{cs_id}/series", json={
        "curve_set_id": cs_id,
        "type": "head",
        "points": points
    })
    assert response.status_code == 200
    series_data = response.json()
    assert series_data["fit_model_type"] == "polynomial_2"
    series_id = series_data["id"]

    # 5. Evaluate Series
    response = client.post(f"/curve-sets/series/{series_id}/evaluate", json={"flow": 50, "head_optional": 25})
    assert response.status_code == 200
    eval_data = response.json()
    assert "head" in eval_data["predictions"]
    # y=x, so 50 -> 50.
    assert abs(eval_data["predictions"]["head"] - 50.0) < 1.0
    assert not eval_data["extrapolation"]

    # 6. Extrapolation check
    response = client.post(f"/curve-sets/series/{series_id}/evaluate", json={"flow": 200})
    assert response.status_code == 200
    eval_data = response.json()
    assert eval_data["extrapolation"]
    assert len(eval_data["warnings"]) > 0

def test_validation_blocking(client):
    # Test blocking error
    points = [{"flow": "bad", "value": 0}]
    response = client.post("/curve-sets/validate", json={"curve_type": "head", "points": points})
    assert response.status_code == 200 # Returns result with errors, not 400
    data = response.json()
    assert len(data["blocking_errors"]) > 0
    assert data["blocking_errors"][0]["code"] == "NON_NUMERIC"
