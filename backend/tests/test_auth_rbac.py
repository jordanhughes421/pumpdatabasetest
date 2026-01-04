from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, StaticPool, select
from backend.main import app, get_session
from backend.models import User, Organization, Membership, UserRole, Pump, Invite
from backend.auth_utils import create_access_token, get_password_hash
import pytest
import datetime

# Setup in-memory DB for tests
# StaticPool is important for in-memory sqlite to persist across threads if needed
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.create_all(engine)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)

@pytest.fixture(name="session")
def session_fixture():
    # Re-create tables to ensure fresh state
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="setup_data")
def setup_data(session: Session):
    # Create Org 1
    org1 = Organization(name="Org 1")
    session.add(org1)
    session.commit()

    # Create Org 2
    org2 = Organization(name="Org 2")
    session.add(org2)
    session.commit()

    # Create Users
    # Admin in Org 1
    admin_user = User(email="admin@org1.com", hashed_password=get_password_hash("password"))
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)

    m1 = Membership(user_id=admin_user.id, org_id=org1.id, role=UserRole.admin)
    session.add(m1)

    # Viewer in Org 1
    viewer_user = User(email="viewer@org1.com", hashed_password=get_password_hash("password"))
    session.add(viewer_user)
    session.commit()
    session.refresh(viewer_user)

    m2 = Membership(user_id=viewer_user.id, org_id=org1.id, role=UserRole.viewer)
    session.add(m2)

    # User in Org 2
    user_org2 = User(email="user@org2.com", hashed_password=get_password_hash("password"))
    session.add(user_org2)
    session.commit()
    session.refresh(user_org2)

    m3 = Membership(user_id=user_org2.id, org_id=org2.id, role=UserRole.admin)
    session.add(m3)

    session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin_user": admin_user,
        "viewer_user": viewer_user,
        "user_org2": user_org2
    }

def test_login(setup_data):
    response = client.post("/auth/login", json={"email": "admin@org1.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@org1.com"

def test_org_scoping(setup_data, session):
    # 1. Admin Org 1 creates a pump
    admin = setup_data["admin_user"]
    token = create_access_token({"sub": admin.email})
    headers = {"Authorization": f"Bearer {token}"}

    pump_data = {"manufacturer": "PumpCo", "model": "ModelX"}
    response = client.post("/pumps/", json=pump_data, headers=headers)
    assert response.status_code == 200
    pump_id = response.json()["id"]

    # 2. User Org 2 tries to read it (should fail or return empty list)
    user2 = setup_data["user_org2"]
    token2 = create_access_token({"sub": user2.email})
    headers2 = {"Authorization": f"Bearer {token2}"}

    # List
    response = client.get("/pumps/", headers=headers2)
    assert response.status_code == 200
    assert len(response.json()) == 0 # Org 2 has no pumps

    # Get specific
    response = client.get(f"/pumps/{pump_id}", headers=headers2)
    assert response.status_code == 404

    # 3. Viewer Org 1 tries to read it (should succeed)
    viewer = setup_data["viewer_user"]
    token3 = create_access_token({"sub": viewer.email})
    headers3 = {"Authorization": f"Bearer {token3}"}

    response = client.get(f"/pumps/{pump_id}", headers=headers3)
    assert response.status_code == 200

def test_rbac_write_protection(setup_data):
    # Viewer tries to create pump
    viewer = setup_data["viewer_user"]
    token = create_access_token({"sub": viewer.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/pumps/", json={"manufacturer": "Fail", "model": "Fail"}, headers=headers)
    assert response.status_code == 403

def test_invite_flow(setup_data, session):
    # Admin creates invite
    admin = setup_data["admin_user"]
    token = create_access_token({"sub": admin.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/orgs/{setup_data['org1'].id}/invites",
                           json={"email": "new@org1.com", "role": "editor"},
                           headers=headers)
    assert response.status_code == 200
    invite_token = response.json()["invite_token"]

    # Verify invite in DB
    invite = session.exec(select(Invite).where(Invite.token == invite_token)).first()
    assert invite is not None
    assert invite.role == UserRole.editor

    # New user (simulate registration)
    new_user = User(email="new@org1.com", hashed_password=get_password_hash("password"))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Need to give them a dummy token to authenticate against /auth/me or others,
    # but redeem requires just authenticated user.
    # Note: `create_access_token` works even without user in DB if we don't validate it in the token generation,
    # but `get_current_user` will check DB.
    new_token = create_access_token({"sub": new_user.email})
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Redeem
    response = client.post(f"/orgs/invites/{invite_token}/redeem", headers=new_headers)
    assert response.status_code == 200

    # Verify membership
    m = session.exec(select(Membership).where(Membership.user_id == new_user.id)).first()
    assert m is not None
    assert m.role == UserRole.editor
    assert m.org_id == setup_data["org1"].id

    # Verify invite is gone
    invite = session.exec(select(Invite).where(Invite.token == invite_token)).first()
    assert invite is None
