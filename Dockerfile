# ═══════════════════════════════════════════════════════════════════
# PulseTech FAERS Backend — Black Box Docker Image
# Layer 10: Compiled .pyc only, no source code exposed
# Copyright (c) 2026 PulseTech (ANC-031). All rights reserved.
# ═══════════════════════════════════════════════════════════════════

# Stage 1: Compile Python to .pyc
FROM python:3.11-slim AS compiler

WORKDIR /compile
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app/
COPY backend/alembic ./alembic/
COPY backend/alembic.ini .

# Compile all .py to .pyc and remove source
RUN python -m compileall -b app/ alembic/ && \
    find app/ alembic/ -name "*.py" -delete

# Stage 2: Production image (only .pyc files)
FROM python:3.11-slim AS production

LABEL maintainer="PulseTech (ANC-031)"
LABEL description="FAERS Pediatric ADR API — Licensed Black Box"
LABEL copyright="2026 MIT Vishwaprayag University. All rights reserved."

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY compiled .pyc files (no source code)
COPY --from=compiler /compile/app ./app/
COPY --from=compiler /compile/alembic ./alembic/
COPY --from=compiler /compile/alembic.ini .

# GNN checkpoints directory
RUN mkdir -p gnn/checkpoints

# Security: non-root user
RUN useradd -m -s /bin/bash pulsetech
USER pulsetech

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
