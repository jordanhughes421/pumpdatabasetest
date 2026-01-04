from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import create_db_and_tables, get_session
from backend.routers import pumps, curves, auth, orgs
from backend.models import User, Organization, Membership, UserRole
from backend.auth_utils import get_password_hash
from sqlmodel import Session, select

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    # Bootstrap default org and admin if not exists
    from backend.database import engine
    with Session(engine) as session:
        if not session.exec(select(Organization)).first():
            print("Bootstrapping default organization...")
            default_org = Organization(name="Default Organization")
            session.add(default_org)
            session.commit()
            session.refresh(default_org)

            # Create admin user
            admin_email = "admin@example.com"
            if not session.exec(select(User).where(User.email == admin_email)).first():
                print("Bootstrapping admin user...")
                admin_user = User(
                    email=admin_email,
                    hashed_password=get_password_hash("admin123"),
                    is_active=True
                )
                session.add(admin_user)
                session.commit()
                session.refresh(admin_user)

                # Add membership
                membership = Membership(
                    user_id=admin_user.id,
                    org_id=default_org.id,
                    role=UserRole.admin
                )
                session.add(membership)
                session.commit()

    yield

app = FastAPI(
    title="Pump Performance Storage",
    lifespan=lifespan
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pumps.router)
app.include_router(curves.router)
app.include_router(orgs.router)

@app.get("/")
def root():
    return {"message": "Pump Performance API is running"}
