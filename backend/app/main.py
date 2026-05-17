"""
PulseTech FAERS Pediatric ADR API — Main Application
Copyright (c) 2026 PulseTech (ANC-031) — MIT Vishwaprayag University.
All rights reserved. Unauthorized reproduction or distribution is prohibited.
"""
import sys
import os
import logging

# Fix Windows terminal encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Logging setup ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pulsetech")

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import upload, demographics, signals, reactions, outcomes, gnn, reports, pdf_export
from app.routers import auth_router
from app.auth import require_auth
from app.security import (
    rate_limit_middleware,
    ip_whitelist_middleware,
    request_logging_middleware,
    license_check_middleware,
    validate_license,
    verify_integrity,
)

# ═══════════════════════════════════════════════════════════════════
# Startup checks (License + Integrity)
# ═══════════════════════════════════════════════════════════════════
license_ok, license_msg = validate_license()
logger.info(f"[LICENSE] {license_msg}")

integrity_ok, integrity_msg = verify_integrity()
logger.info(f"[INTEGRITY] {integrity_msg}")

if not integrity_ok:
    logger.critical("[SHUTDOWN] Integrity check failed. Server will NOT accept requests.")

# ═══════════════════════════════════════════════════════════════════
# Pre-warm Cache
# ═══════════════════════════════════════════════════════════════════
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.database import sync_session_factory
from app.core.cache import get_cached_report, set_cached_report

def prewarm_report_cache_sync():
    """Pre-compute and cache reports for all quarters on startup."""
    db = sync_session_factory()
    try:
        # Get all quarters from metadata table
        quarters = db.execute(
            text("SELECT quarter FROM loaded_quarters ORDER BY quarter")
        ).scalars().all()

        combos = [(None, None)]  # ALL quarters, all age groups
        age_groups = ["ADOLESCENT", "CHILD", "INFANT", "NEONATE"]

        for q in quarters:
            combos.append((q, None))
            for ag in age_groups:
                combos.append((q, ag))
        combos.append((None, None))

        for quarter, age_group in combos:
            if get_cached_report(quarter, age_group):
                continue
            result = db.execute(
                text("SELECT compute_faers_report(:quarter, :age_group)"),
                {"quarter": quarter, "age_group": age_group}
            ).scalar()
            set_cached_report(quarter, age_group, dict(result))
            db.commit()
    except Exception as e:
        logger.error(f"[prewarm] Error: {e}")
    finally:
        db.close()

async def prewarm_report_cache():
    import asyncio
    await asyncio.to_thread(prewarm_report_cache_sync)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run prewarm in background thread — don't block server startup
    asyncio.create_task(prewarm_report_cache())
    yield

# ═══════════════════════════════════════════════════════════════════
# App Creation
# ═══════════════════════════════════════════════════════════════════
app = FastAPI(
    title="FAERS Pediatric ADR API",
    description="PulseTech FAERS Pediatric Adverse Drug Reaction Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if os.getenv("PULSETECH_PRODUCTION") else "/docs",
    redoc_url=None if os.getenv("PULSETECH_PRODUCTION") else "/redoc",
)

# ── Layer 8: CORS — env-driven allowed origin ──────────────────────
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")
allowed_origins = [o.strip() for o in ALLOWED_ORIGIN.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Middleware Stack (order matters: last added = first executed) ───
# Layer 9: Request Logging (audit trail)
app.middleware("http")(request_logging_middleware)

# Layer 11: License Check
app.middleware("http")(license_check_middleware)

# Layer 6: Rate Limiting
app.middleware("http")(rate_limit_middleware)

# Layer 7: IP Whitelist
app.middleware("http")(ip_whitelist_middleware)


# ── Security Headers on every response ──────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "PulseTech ANC-031"
    response.headers["X-Copyright"] = "2026 MIT Vishwaprayag University. All rights reserved."
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    return response


# ── Public routes (no auth needed) ──────────────────────────────────
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])

# ── Protected routes (JWT + IP binding + fingerprint required) ──────
app.include_router(upload.router, prefix="/api/upload", tags=["upload"], dependencies=[Depends(require_auth)])
app.include_router(demographics.router, prefix="/api/demographics", tags=["demographics"], dependencies=[Depends(require_auth)])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"], dependencies=[Depends(require_auth)])
app.include_router(reactions.router, prefix="/api/reactions", tags=["reactions"], dependencies=[Depends(require_auth)])
app.include_router(outcomes.router, prefix="/api/outcomes", tags=["outcomes"], dependencies=[Depends(require_auth)])
app.include_router(gnn.router, prefix="/api/gnn", tags=["gnn"], dependencies=[Depends(require_auth)])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"], dependencies=[Depends(require_auth)])
app.include_router(pdf_export.router, prefix="/api/reports", tags=["PDF Export"], dependencies=[Depends(require_auth)])

@app.get("/api/health")
async def health_check():
    """Health check endpoint (public)."""
    import socket

    pg_status = "disconnected"
    try:
        s = socket.create_connection(("localhost", 5432), timeout=2)
        s.close()
        pg_status = "connected"
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "FAERS Pediatric ADR API",
        "copyright": "2026 PulseTech (ANC-031) MIT Vishwaprayag University",
        "license": license_msg,
        "integrity": integrity_msg,
        "postgresql": pg_status,
    }
