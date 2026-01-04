from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, StaticPool
from backend.main import app, get_session
from backend.dependencies import get_current_user, get_active_org, RequireRole, get_current_role
from backend.models import User, Organization, Membership, UserRole
import pytest

# Setup in-memory DB for tests
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.create_all(engine)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Auth overrides
def override_get_current_user():
    return User(id=1, email="test@example.com", is_active=True, hashed_password="pw")

def override_get_active_org():
    return Organization(id=1, name="Test Org")

def override_get_current_role():
    return UserRole.admin

def override_require_role(role):
    # This is tricky because RequireRole is a class called with Depends
    # But usually we can override the dependency it returns if we know the signature.
    # Actually, RequireRole returns a callable.
    # In endpoints: role: UserRole = Depends(RequireRole({UserRole.editor, UserRole.admin}))
    # We can override the Dependency that resolves to `UserRole`?
    # No, RequireRole(...) is the dependency.
    # We can override the `get_current_role` dependency used by `RequireRole`.
    return UserRole.admin

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_active_org] = override_get_active_org
app.dependency_overrides[get_current_role] = override_get_current_role

@pytest.fixture(name="client")
def client_fixture():
    # Reset DB
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    # Create Org manually because get_active_org returns a mock object,
    # but foreign keys need it to exist in DB for writes?
    # Endpoints use `org.id` from the dependency.
    # If the DB is empty, `Pump(org_id=1)` will fail foreign key constraint if enabled.
    # SQLite by default might not enforce FKs unless enabled. SQLModel enables them usually?
    # Let's insert the org into the DB to be safe.
    with Session(engine) as session:
        org = Organization(id=1, name="Test Org")
        session.add(org)
        session.commit()

    return TestClient(app)

def test_create_pump(client: TestClient):
    response = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model", "meta_data": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["manufacturer"] == "Test Mfg"
    assert data["org_id"] == 1

def test_read_pumps(client: TestClient):
    client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    response = client.get("/pumps/")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_create_curve_set(client: TestClient):
    # Create pump first
    pump_res = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    assert pump_res.status_code == 200
    pump_id = pump_res.json()["id"]

    response = client.post(
        "/curve-sets/",
        json={
            "name": "Test Set",
            "pump_id": pump_id,
            "units": {"flow": "gpm", "head": "ft"}
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Set"

def test_add_series(client: TestClient):
    # Create pump & curve set
    pump_res = client.post(
        "/pumps/",
        json={"manufacturer": "Test Mfg", "model": "Test Model"}
    )
    pump_id = pump_res.json()["id"]

    cs_res = client.post(
        "/curve-sets/",
        json={
            "name": "Test Set",
            "pump_id": pump_id
        }
    )
    cs_id = cs_res.json()["id"]

    # Add series
    series_res = client.post(
        f"/curve-sets/{cs_id}/series",
        json={
            "curve_set_id": cs_id,
            "type": "head",
            "points": [
                {"flow": 0, "value": 100},
                {"flow": 100, "value": 80}
            ]
        }
    )
    assert series_res.status_code == 200
    assert series_res.json()["type"] == "head"
    assert len(series_res.json()["points"]) == 2
