"""Clerk webhook — sync user.created / user.updated to DB."""

import os
import hashlib
import hmac
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db_session
from core.db.repositories.user_repo import UserRepository

router = APIRouter()

CLERK_WEBHOOK_SECRET: Optional[str] = os.getenv("CLERK_WEBHOOK_SECRET")


# ─── Payload schemas ──────────────────────────────────────────────────────────

class ClerkEmailAddress(BaseModel):
    email_address: str
    primary: Optional[bool] = False


class ClerkUserData(BaseModel):
    id: str
    email_addresses: list[ClerkEmailAddress]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image_url: Optional[str] = None


class ClerkEvent(BaseModel):
    type: str
    data: ClerkUserData


# ─── Svix signature verification ─────────────────────────────────────────────

def _verify_svix_signature(request_headers: dict, body: bytes) -> bool:
    """
    Verify Svix webhook signature.
    Header format: svix-id, svix-timestamp, svix-signature
    Signed string: "{svix_id}.{svix_timestamp}.{body}"
    """
    if not CLERK_WEBHOOK_SECRET:
        return False  # fail closed: unsigned webhooks are never trusted

    svix_id = request_headers.get("svix-id", "")
    svix_ts = request_headers.get("svix-timestamp", "")
    svix_sig = request_headers.get("svix-signature", "")

    if not (svix_id and svix_ts and svix_sig):
        return False

    # Reject timestamps older than 5 minutes
    try:
        if abs(time.time() - int(svix_ts)) > 300:
            return False
    except ValueError:
        return False

    # Strip "whsec_" prefix and base64-decode the secret
    import base64
    secret_bytes = base64.b64decode(CLERK_WEBHOOK_SECRET.removeprefix("whsec_"))
    signed_content = f"{svix_id}.{svix_ts}.".encode() + body
    expected = hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected).decode()

    # svix-signature may contain multiple space-separated "v1,<sig>" values
    for sig_entry in svix_sig.split(" "):
        parts = sig_entry.split(",", 1)
        if len(parts) == 2 and parts[0] == "v1" and hmac.compare_digest(parts[1], expected_b64):
            return True
    return False


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    session: Session = Depends(get_db_session),
):
    if not CLERK_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    body = await request.body()

    if not _verify_svix_signature(dict(request.headers), body):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        import json
        payload = json.loads(body)
        event = ClerkEvent(**payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    repo = UserRepository(session)

    primary_email = next(
        (e.email_address for e in event.data.email_addresses if e.primary),
        event.data.email_addresses[0].email_address if event.data.email_addresses else None,
    )

    if event.type == "user.created":
        if not primary_email:
            raise HTTPException(status_code=400, detail="No email in payload")

        repo.upsert_from_clerk(
            clerk_id=event.data.id,
            email=primary_email,
            first_name=event.data.first_name,
            last_name=event.data.last_name,
            image_url=event.data.image_url,
        )
        return {"message": "User created", "clerk_id": event.data.id}

    elif event.type == "user.updated":
        user = repo.get_by_clerk_id(event.data.id)
        if user:
            if primary_email:
                user.email = primary_email
            user.first_name = event.data.first_name
            user.last_name = event.data.last_name
            user.image_url = event.data.image_url
        return {"message": "User updated" if user else "User not found"}

    elif event.type == "user.deleted":
        user = repo.get_by_clerk_id(event.data.id)
        if user:
            session.delete(user)
        return {"message": "User deleted" if user else "User not found"}

    return {"message": f"Event '{event.type}' ignored"}
