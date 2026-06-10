"""
PulseTech Backend Obfuscation Script
=====================================
Uses PyArmor to obfuscate all Python source files in the app/ directory.
The obfuscated output is placed in dist_protected/ — original files are UNTOUCHED.

Usage:
    python build_protected.py

Output:
    dist_protected/
        app/          ← obfuscated Python files (encrypted bytecode)
        .env.dist     ← sanitized env template
        requirements.txt
        stored_proc.sql

Copyright (c) 2026 PulseTech (ANC-031). All rights reserved.
"""
import os
import sys
import shutil
import subprocess
import hashlib
import glob
import time

sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BACKEND_DIR, "app")
OUTPUT_DIR = os.path.join(BACKEND_DIR, "dist_protected")

# Files/folders to include in distribution (non-Python assets)
EXTRA_FILES = [
    "requirements.txt",
    "stored_proc.sql",
    "alembic.ini",
]

EXTRA_DIRS = [
    "alembic",
]

# Files to EXCLUDE from distribution
EXCLUDE_PATTERNS = [
    "*.log",
    "*.pdf",
    "*.txt",
    "__pycache__",
    ".pyre_configuration",
    "pyrightconfig.json",
    "test_*.py",
    "check_*.py",
    "fix_*.py",
    "debug.py",
    "clean_*.py",
    "kill_*.py",
    "seed.py",
    "warm_*.py",
    "upload_*.py",
    "fast_*.py",
    "revert_*.py",
    "run_sql.py",
    "paper_*.py",
    "parse_*.py",
    "batch_*.py",
    "headers.txt",
]


def banner(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def clean_output():
    """Remove previous obfuscated output."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        print(f"  Cleaned previous output: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def obfuscate_app():
    """Use PyArmor to obfuscate the app/ directory."""
    banner("STEP 1: Obfuscating Python Source (PyArmor)")

    # PyArmor v9.x CLI command - obfuscates all .py files recursively
    cmd = [
        "pyarmor", "gen",
        "--output", os.path.join(OUTPUT_DIR),
        "--recursive",
        "--obf-module", "1",
        "--obf-code", "1",
        APP_DIR,
    ]

    print(f"  Command: {' '.join(cmd)}")
    t0 = time.perf_counter()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=BACKEND_DIR, shell=True)
        if result.returncode != 0:
            print(f"  [!] PyArmor standard mode failed, trying minimal mode...")
            print(f"  stderr: {result.stderr[:500]}")

            # Fallback: minimal obfuscation
            cmd_basic = [
                "pyarmor", "gen",
                "--output", os.path.join(OUTPUT_DIR),
                "--recursive",
                "--obf-code", "0",
                APP_DIR,
            ]
            result = subprocess.run(cmd_basic, capture_output=True, text=True, cwd=BACKEND_DIR, shell=True)
            if result.returncode != 0:
                print(f"  [X] PyArmor failed!")
                print(f"  stdout: {result.stdout[:300]}")
                print(f"  stderr: {result.stderr[:500]}")
                return False

        elapsed = time.perf_counter() - t0
        print(f"  [OK] Obfuscation complete in {elapsed:.1f}s")
        if result.stdout:
            print(f"  stdout: {result.stdout[:300]}")
        return True

    except FileNotFoundError:
        print("  [X] PyArmor not found. Install with: pip install pyarmor")
        return False


def copy_extra_files():
    """Copy non-Python files needed for distribution."""
    banner("STEP 2: Copying Extra Files")

    for f in EXTRA_FILES:
        src = os.path.join(BACKEND_DIR, f)
        if os.path.exists(src):
            dst = os.path.join(OUTPUT_DIR, f)
            shutil.copy2(src, dst)
            print(f"  ✓ Copied: {f}")

    for d in EXTRA_DIRS:
        src = os.path.join(BACKEND_DIR, d)
        if os.path.exists(src):
            dst = os.path.join(OUTPUT_DIR, d)
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  ✓ Copied dir: {d}/")


def create_sanitized_env():
    """Create .env.dist with placeholder credentials."""
    banner("STEP 3: Creating Sanitized .env")

    env_dist = os.path.join(OUTPUT_DIR, ".env.dist")
    content = """# ═══════════════════════════════════════════════════════════════════
# PulseTech FAERS Pediatric ADR — Configuration (TEMPLATE)
# ═══════════════════════════════════════════════════════════════════
# IMPORTANT: Copy this file to .env and fill in your own values.
# DO NOT commit .env to version control.

DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/faers_pediatric
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/faers_pediatric
REDIS_URL=redis://localhost:6379/0
RXNORM_API_BASE=https://rxnav.nlm.nih.gov/REST
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_256BIT_KEY

SKIP_RXNORM=1
GNN_CHECKPOINT_DIR=./gnn/checkpoints/
GNN_DEVICE=cuda
SIGNAL_MIN_N=3

# ═══════════════════════════════════════════════════════════════════
# SECURITY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
PULSETECH_SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_SECRET
PULSETECH_ADMIN_USER=CHANGE_ME
PULSETECH_ADMIN_PASS=CHANGE_ME
ALLOWED_ORIGIN=http://localhost:5173
PULSETECH_IP_WHITELIST=
PULSETECH_RATE_LIMIT=100
PULSETECH_LICENSE_KEY=
PULSETECH_LICENSE_EXPIRY=2027-12-31
PULSETECH_PRODUCTION=1
PULSETECH_AUDIT_LOG=security_audit.log
"""
    with open(env_dist, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Created: .env.dist (credentials sanitized)")


def generate_integrity_hash():
    """Generate SHA256 hash of all obfuscated .py files."""
    banner("STEP 4: Generating Integrity Hash")

    hasher = hashlib.sha256()
    py_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "**", "*.py"), recursive=True))

    for filepath in py_files:
        with open(filepath, "rb") as f:
            hasher.update(f.read())

    digest = hasher.hexdigest()
    hash_file = os.path.join(OUTPUT_DIR, "integrity.sha256")
    with open(hash_file, "w") as f:
        f.write(digest)

    print(f"  ✓ Hash: {digest[:32]}...")
    print(f"  ✓ Saved to: integrity.sha256")
    print(f"  ✓ Files hashed: {len(py_files)}")
    return digest


def print_summary():
    """Print final summary of the protected distribution."""
    banner("DISTRIBUTION SUMMARY")

    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(OUTPUT_DIR):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            fp = os.path.join(root, f)
            size = os.path.getsize(fp)
            total_files += 1
            total_size += size

    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Total files:      {total_files}")
    print(f"  Total size:       {total_size / (1024*1024):.1f} MB")
    print(f"\n  ✅ Protected backend ready for distribution!")
    print(f"  ⚠  Original source code is UNTOUCHED.")
    print(f"\n  To test the protected build:")
    print(f"    cd dist_protected")
    print(f"    copy .env.dist .env  (then fill in credentials)")
    print(f"    uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    banner("PulseTech Backend Protection Builder")
    print(f"  Backend dir: {BACKEND_DIR}")
    print(f"  App dir:     {APP_DIR}")
    print(f"  Output dir:  {OUTPUT_DIR}")

    clean_output()

    if not obfuscate_app():
        print("\n❌ Obfuscation failed. Aborting.")
        sys.exit(1)

    copy_extra_files()
    create_sanitized_env()
    generate_integrity_hash()
    print_summary()
