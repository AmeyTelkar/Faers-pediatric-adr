"""
Login router for PulseTech authentication.
Copyright (c) 2026 PulseTech (ANC-031). All rights reserved.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.auth import ADMIN_USERNAME, ADMIN_PASSWORD_HASH, verify_password, create_access_token
import logging

router = APIRouter()
logger = logging.getLogger("pulsetech.auth")

# ── Track failed login attempts for brute-force protection ──────────
_failed_attempts: dict[str, list] = {}
MAX_FAILED = 5
LOCKOUT_MINUTES = 15


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_in: int = 43200


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    """Authenticate admin user and return JWT token with IP binding."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # ── Brute-force protection ──────────────────────────────────────
    from datetime import datetime, timedelta
    now = datetime.now()
    if client_ip in _failed_attempts:
        # Clean old attempts
        _failed_attempts[client_ip] = [t for t in _failed_attempts[client_ip] if now - t < timedelta(minutes=LOCKOUT_MINUTES)]
        if len(_failed_attempts[client_ip]) >= MAX_FAILED:
            logger.warning(f"[SECURITY] BRUTE FORCE LOCKOUT: IP={client_ip}, attempts={len(_failed_attempts[client_ip])}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes."
            )

    # ── Credential check ────────────────────────────────────────────
    if req.username != ADMIN_USERNAME or not verify_password(req.password, ADMIN_PASSWORD_HASH):
        _failed_attempts.setdefault(client_ip, []).append(now)
        remaining = MAX_FAILED - len(_failed_attempts.get(client_ip, []))
        logger.warning(f"[SECURITY] FAILED LOGIN: user='{req.username}', ip={client_ip}, remaining={remaining}")
        raise HTTPException(status_code=401, detail=f"Invalid credentials. {remaining} attempts remaining.")

    # ── Success — clear failed attempts and issue token ──────────────
    _failed_attempts.pop(client_ip, None)
    token = create_access_token(req.username, client_ip, user_agent)
    logger.info(f"[AUTH] LOGIN SUCCESS: user={req.username}, ip={client_ip}")
    return LoginResponse(access_token=token, username=req.username)


@router.get("/verify")
async def verify_token():
    """Public endpoint to check if the server is alive."""
    return {"status": "ok", "service": "PulseTech Auth"}
