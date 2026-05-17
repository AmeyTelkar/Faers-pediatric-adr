"""
PulseTech Security Middleware Stack.
Layers: Rate Limiting, IP Whitelist, Request Logging, License Validation.
Copyright (c) 2026 PulseTech (ANC-031). All rights reserved.
"""
import os
import time
import hashlib
import logging
from collections import defaultdict
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("pulsetech.security")

# ═══════════════════════════════════════════════════════════════════
# Layer 6: Rate Limiting (100 req/min per IP)
# ═══════════════════════════════════════════════════════════════════
RATE_LIMIT = int(os.getenv("PULSETECH_RATE_LIMIT", "100"))
RATE_WINDOW = 60  # seconds

_request_log: dict[str, list[float]] = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Clean old entries
    _request_log[client_ip] = [t for t in _request_log[client_ip] if now - t < RATE_WINDOW]
    _request_log[client_ip].append(now)

    if len(_request_log[client_ip]) > RATE_LIMIT:
        logger.warning(f"[RATE LIMIT] IP={client_ip}, count={len(_request_log[client_ip])}/{RATE_LIMIT}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Maximum 100 requests per minute."},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT - len(_request_log[client_ip])))
    return response


# ═══════════════════════════════════════════════════════════════════
# Layer 7: IP Whitelist
# ═══════════════════════════════════════════════════════════════════
_raw = os.getenv("PULSETECH_IP_WHITELIST", "")
IP_WHITELIST = [ip.strip() for ip in _raw.split(",") if ip.strip()] if _raw else []


async def ip_whitelist_middleware(request: Request, call_next):
    # If whitelist is empty, allow all (dev mode)
    if not IP_WHITELIST:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    # Always allow localhost
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)

    if client_ip not in IP_WHITELIST:
        logger.warning(f"[IP BLOCKED] {client_ip} not in whitelist")
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied. Your IP is not authorized."},
        )

    return await call_next(request)


# ═══════════════════════════════════════════════════════════════════
# Layer 9: Request Logging (audit trail)
# ═══════════════════════════════════════════════════════════════════
_LOG_FILE = os.getenv("PULSETECH_AUDIT_LOG", "security_audit.log")
_audit_logger = logging.getLogger("pulsetech.audit")
_audit_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
_audit_logger.addHandler(_audit_handler)
_audit_logger.setLevel(logging.INFO)


async def request_logging_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    start = time.time()

    response = await call_next(request)

    elapsed = round((time.time() - start) * 1000, 1)
    status_code = response.status_code

    # Extract user from auth header if present
    auth = request.headers.get("authorization", "")
    user = "anonymous"
    if auth.startswith("Bearer "):
        try:
            import jwt
            payload = jwt.decode(auth[7:], options={"verify_signature": False})
            user = payload.get("sub", "unknown")
        except Exception:
            user = "invalid_token"

    _audit_logger.info(f"IP={client_ip} | USER={user} | {method} {path} | {status_code} | {elapsed}ms")

    return response


# ═══════════════════════════════════════════════════════════════════
# Layer 11: License Key Validation
# ═══════════════════════════════════════════════════════════════════
LICENSE_KEY = os.getenv("PULSETECH_LICENSE_KEY", "")
LICENSE_EXPIRY = os.getenv("PULSETECH_LICENSE_EXPIRY", "2027-12-31")
LICENSE_VALID = True


def validate_license() -> tuple[bool, str]:
    """Validate license on startup. Returns (valid, message)."""
    global LICENSE_VALID

    if not LICENSE_KEY:
        # Dev mode — no license required
        LICENSE_VALID = True
        return True, "Development mode (no license key set)"

    # Check expiry
    try:
        expiry = datetime.strptime(LICENSE_EXPIRY, "%Y-%m-%d")
        if datetime.now() > expiry:
            LICENSE_VALID = False
            return False, f"License expired on {LICENSE_EXPIRY}"
    except ValueError:
        LICENSE_VALID = False
        return False, "Invalid license expiry format"

    # Verify key hash
    expected_hash = hashlib.sha256(f"PULSETECH-ANC031-{LICENSE_EXPIRY}".encode()).hexdigest()[:32]
    if LICENSE_KEY != expected_hash:
        LICENSE_VALID = False
        return False, "Invalid license key"

    LICENSE_VALID = True
    return True, f"License valid until {LICENSE_EXPIRY}"


async def license_check_middleware(request: Request, call_next):
    """Block all requests if license is expired (returns 423 Locked)."""
    if not LICENSE_VALID:
        # Allow only health check and login
        if request.url.path in ("/api/health", "/api/auth/login", "/api/auth/verify"):
            return await call_next(request)
        return JSONResponse(
            status_code=423,
            content={
                "detail": "PulseTech license has expired. Contact support@pulsetech-adr.com to renew.",
                "license_status": "expired",
            },
        )
    return await call_next(request)


# ═══════════════════════════════════════════════════════════════════
# Layer 12: File Integrity Check
# ═══════════════════════════════════════════════════════════════════
_INTEGRITY_FILE = os.getenv("PULSETECH_INTEGRITY_FILE", "")


def compute_integrity_hash(directory: str = "app") -> str:
    """Compute SHA256 hash of all .py files in the app directory."""
    import glob
    hasher = hashlib.sha256()
    for filepath in sorted(glob.glob(f"{directory}/**/*.py", recursive=True)):
        with open(filepath, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()


def verify_integrity() -> tuple[bool, str]:
    """Verify backend code hasn't been tampered with."""
    if not _INTEGRITY_FILE:
        return True, "Integrity check skipped (no baseline file)"

    try:
        with open(_INTEGRITY_FILE, "r") as f:
            expected = f.read().strip()
        actual = compute_integrity_hash()
        if actual != expected:
            logger.critical(f"[INTEGRITY] CODE TAMPERED! Expected={expected[:16]}... Got={actual[:16]}...")
            return False, "Integrity check FAILED — code has been modified"
        return True, "Integrity check passed"
    except FileNotFoundError:
        return True, "No integrity baseline found"
