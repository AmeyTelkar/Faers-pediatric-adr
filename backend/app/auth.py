"""
Authentication module for PulseTech FAERS Dashboard.
JWT-based auth with bcrypt hashing, IP binding, and session fingerprinting.
Copyright (c) 2026 PulseTech (ANC-031) — MIT Vishwaprayag University.
All rights reserved. Unauthorized access is prohibited.
"""
import os
import jwt
import bcrypt
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("pulsetech.auth")

# ── Config ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("PULSETECH_SECRET_KEY", "PT-ANC031-FAERS-2026-SECRET-KEY-DO-NOT-SHARE")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12

# ── Admin credentials (bcrypt hashed) ───────────────────────────────
ADMIN_USERNAME = os.getenv("PULSETECH_ADMIN_USER", "FEARS")
ADMIN_PASSWORD_HASH = bcrypt.hashpw(
    os.getenv("PULSETECH_ADMIN_PASS", "AMAR@2498").encode("utf-8"),
    bcrypt.gensalt()
).decode("utf-8")

# ── IP Whitelist (empty = allow all, for dev) ───────────────────────
_raw_whitelist = os.getenv("PULSETECH_IP_WHITELIST", "")
IP_WHITELIST = [ip.strip() for ip in _raw_whitelist.split(",") if ip.strip()] if _raw_whitelist else []

security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(username: str, client_ip: str, user_agent: str = "") -> str:
    """Create JWT with IP binding and browser fingerprint."""
    fingerprint = hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]
    payload = {
        "sub": username,
        "bound_ip": client_ip,
        "fingerprint": fingerprint,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iss": "PulseTech-ANC031",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


async def require_auth(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """FastAPI dependency — validates JWT, IP binding, and fingerprint."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    # ── IP Binding Check (Layer 14) ─────────────────────────────────
    client_ip = request.client.host if request.client else "unknown"
    bound_ip = payload.get("bound_ip")
    if bound_ip and bound_ip != client_ip:
        logger.warning(f"[SECURITY] IP MISMATCH: token bound to {bound_ip}, request from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Security violation: IP address mismatch. Token revoked.",
        )

    # ── Fingerprint Check (Layer 13) ────────────────────────────────
    user_agent = request.headers.get("user-agent", "")
    expected_fp = hashlib.sha256(f"{client_ip}:{user_agent}".encode()).hexdigest()[:16]
    token_fp = payload.get("fingerprint")
    if token_fp and token_fp != expected_fp:
        logger.warning(f"[SECURITY] FINGERPRINT MISMATCH: user={payload.get('sub')}, ip={client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Security violation: Browser fingerprint mismatch. Token revoked.",
        )

    return payload
