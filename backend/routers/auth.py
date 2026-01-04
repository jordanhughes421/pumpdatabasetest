from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from backend.database import get_session
from backend.models import User, UserLogin, Token, UserRole, Membership, Organization, UserRead, OrganizationRead
from backend.auth_utils import verify_password, create_access_token, get_password_hash
from backend.dependencies import get_current_user, get_active_org, get_current_role

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(user_in: UserLogin, session: Session = Depends(get_session)):
    # Check if user exists
    existing_user = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create User
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        created_at=datetime.utcnow()
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create default Organization for this user
    org_name = f"{user_in.email.split('@')[0]}'s Org"
    org = Organization(name=org_name, created_at=datetime.utcnow())
    session.add(org)
    session.commit()
    session.refresh(org)

    # Add Membership as Admin
    membership = Membership(
        user_id=user.id,
        org_id=org.id,
        role=UserRole.admin,
        created_at=datetime.utcnow()
    )
    session.add(membership)
    session.commit()

    # Generate Token
    access_token = create_access_token(data={"sub": user.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user,
        active_org=org,
        role=UserRole.admin
    )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    user.last_login_at = datetime.utcnow()
    session.add(user)
    session.commit()

    # Get active org (logic duplicated from dependency essentially, but we need it for the token response)
    # We just pick the first one for the login response default.
    memberships = session.exec(select(Membership).where(Membership.user_id == user.id)).all()
    if not memberships:
         raise HTTPException(status_code=403, detail="User has no organizations")

    active_org = memberships[0].organization
    role = memberships[0].role

    access_token = create_access_token(data={"sub": user.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user,
        active_org=active_org,
        role=role
    )

@router.get("/me", response_model=Token)
def read_users_me(
    user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_org),
    role: UserRole = Depends(get_current_role)
):
    # Re-issue token logic isn't here, just return current state
    # But for simplicity, we reuse the Token model to send back user info + context
    return Token(
        access_token="", # Client can ignore this or we can issue a new one
        token_type="bearer",
        user=user,
        active_org=active_org,
        role=role
    )
