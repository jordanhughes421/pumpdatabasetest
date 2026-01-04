from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid

from backend.database import get_session
from backend.models import (
    User, UserRead, Organization, OrganizationRead, Membership, MembershipRead, UserRole, Invite
)
from backend.dependencies import get_current_user, get_active_org, RequireRole, get_current_role
from backend.auth_utils import get_password_hash

router = APIRouter(prefix="/orgs", tags=["orgs"])

@router.get("/{org_id}/members", response_model=List[MembershipRead])
def read_members(
    org_id: int,
    session: Session = Depends(get_session),
    active_org: Organization = Depends(get_active_org),
    role: UserRole = Depends(RequireRole({UserRole.admin}))
):
    if active_org.id != org_id:
        raise HTTPException(status_code=403, detail="Cannot access other organization's members")

    memberships = session.exec(select(Membership).where(Membership.org_id == org_id)).all()
    return memberships

@router.patch("/{org_id}/members/{user_id}", response_model=MembershipRead)
def update_member_role(
    org_id: int,
    user_id: int,
    role_update: UserRole = Body(..., embed=True),
    session: Session = Depends(get_session),
    active_org: Organization = Depends(get_active_org),
    current_role: UserRole = Depends(RequireRole({UserRole.admin})),
    current_user: User = Depends(get_current_user)
):
    if active_org.id != org_id:
        raise HTTPException(status_code=403, detail="Cannot access other organization's members")

    membership = session.exec(
        select(Membership)
        .where(Membership.org_id == org_id)
        .where(Membership.user_id == user_id)
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    # Corrected check
    if membership.user_id == current_user.id:
         pass # Admin can change their own role, but warning: they might lock themselves out. Allowed for MVP.

    membership.role = role_update
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership

@router.delete("/{org_id}/members/{user_id}")
def remove_member(
    org_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    active_org: Organization = Depends(get_active_org),
    role: UserRole = Depends(RequireRole({UserRole.admin}))
):
    if active_org.id != org_id:
        raise HTTPException(status_code=403, detail="Cannot access other organization's members")

    membership = session.exec(
        select(Membership)
        .where(Membership.org_id == org_id)
        .where(Membership.user_id == user_id)
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    session.delete(membership)
    session.commit()
    return {"ok": True}

@router.post("/{org_id}/invites")
def create_invite(
    org_id: int,
    email: str = Body(..., embed=True),
    role: UserRole = Body(..., embed=True),
    session: Session = Depends(get_session),
    active_org: Organization = Depends(get_active_org),
    current_role: UserRole = Depends(RequireRole({UserRole.admin}))
):
    if active_org.id != org_id:
        raise HTTPException(status_code=403, detail="Cannot access other organization's invites")

    token = str(uuid.uuid4())

    invite = Invite(
        org_id=org_id,
        role=role,
        email=email,
        expires_at=datetime.utcnow() + timedelta(days=1),
        token=token
    )
    session.add(invite)
    session.commit()

    # MVP: Return the link directly
    return {"invite_token": token, "invite_url": f"/invites/{token}"} # Frontend will handle the full URL

@router.post("/invites/{token}/redeem")
def redeem_invite(
    token: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    invite = session.exec(select(Invite).where(Invite.token == token)).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invite")

    if datetime.utcnow() > invite.expires_at:
        session.delete(invite)
        session.commit()
        raise HTTPException(status_code=400, detail="Invite expired")

    # Check if user is already a member
    existing = session.exec(
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.org_id == invite.org_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    # Create membership
    membership = Membership(
        user_id=user.id,
        org_id=invite.org_id,
        role=invite.role
    )
    session.add(membership)
    session.delete(invite) # Consume invite
    session.commit()

    return {"ok": True, "org_id": invite.org_id}
