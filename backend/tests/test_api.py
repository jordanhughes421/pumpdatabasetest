from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest

from backend.main import app
from backend.database import get_session
from backend.models import Pump, CurveSet, SeriesType

# Setup in-memory database for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_pump(client: TestClient):
    response = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model", "meta_data": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["manufacturer"] == "Test Mfg"
    assert data["model"] == "Test Model"
    assert "id" in data

def test_read_pumps(client: TestClient):
    client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    response = client.get("/pumps/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["manufacturer"] == "Test Mfg"

def test_create_curve_set(client: TestClient):
    # Create pump first
    pump_res = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    pump_id = pump_res.json()["id"]

    # Create curve set
    response = client.post(
        "/curve-sets/",
        json={
            "name": "Test Curve",
            "pump_id": pump_id,
            "units": {"flow": "gpm", "head": "ft"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Curve"
    assert data["pump_id"] == pump_id

def test_add_series(client: TestClient):
    # Create pump & curve set
    pump_res = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    pump_id = pump_res.json()["id"]

    cs_res = client.post(
        "/curve-sets/",
        json={"name": "Test Curve", "pump_id": pump_id}
    )
    cs_id = cs_res.json()["id"]

    # Add series
    series_data = {
        "curve_set_id": cs_id,
        "type": "head",
        "points": [
            {"series_id": 0, "flow": 0, "value": 100, "sequence": 0},
            {"series_id": 0, "flow": 100, "value": 90, "sequence": 1}
        ]
    }
    response = client.post(f"/curve-sets/{cs_id}/series", json=series_data)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "head"
    assert len(data["points"]) == 2
    assert data["points"][0]["value"] == 100
