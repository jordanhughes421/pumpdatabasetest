from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import User, Organization, Membership, UserRole
from backend.auth_utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user

def get_active_org(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    x_org_id: Optional[str] = Header(None)
) -> Organization:
    # MVP: If user has 1 org, return it. If multiple, check header. If header missing, return first.
    # Logic:
    # 1. Get all memberships for user.
    # 2. If x_org_id is provided, verify membership.
    # 3. If x_org_id not provided, pick first.

    memberships = session.exec(select(Membership).where(Membership.user_id == current_user.id)).all()

    if not memberships:
        raise HTTPException(status_code=403, detail="User is not a member of any organization")

    if x_org_id:
        try:
            target_org_id = int(x_org_id)
            for m in memberships:
                if m.org_id == target_org_id:
                    return m.organization
            raise HTTPException(status_code=403, detail="User is not a member of the requested organization")
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid X-Org-ID header")

    # Default to first org if no header
    return memberships[0].organization

def get_current_role(
    current_user: Annotated[User, Depends(get_current_user)],
    active_org: Annotated[Organization, Depends(get_active_org)],
    session: Session = Depends(get_session)
) -> UserRole:
    membership = session.exec(
        select(Membership)
        .where(Membership.user_id == current_user.id)
        .where(Membership.org_id == active_org.id)
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Membership not found")
    return membership.role

class RequireRole:
    def __init__(self, allowed_roles: set[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, role: Annotated[UserRole, Depends(get_current_role)]):
        if role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return role
