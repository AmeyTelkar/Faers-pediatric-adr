# PulseTech FAERS Pediatric ADR Dashboard

**Research-grade pharmacovigilance dashboard** for analyzing Adverse Drug Reactions (ADR) in the pediatric population using FDA FAERS data.

## Team: PulseTech (ANC-031)

## Tech Stack

| Layer | Technology |
|-------|-----------| 
| Frontend | React 18 + Vite + TailwindCSS 3 |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL 16 |
| Task Queue | Celery + Redis |
| ML/GNN | PyTorch + PyTorch Geometric (HANConv) |
| Analytics | PRR, ROR, IC (WHO-UMC), EBGM (DuMouchel GPS) |

## Features

- **ETL Pipeline**: Ingest 7 FAERS file types ($-delimited), auto-detect schema, dedup, normalize
- **Pediatric Filter**: ICH E11 age bands (Neonate, Infant, Child, Adolescent)
- **Data Cleaning**: role_cod='DN' removal, route normalization, expanded INDI unknown cleaning
- **Signal Detection**: 4 disproportionality measures with 2×2 contingency tables
- **GNN Predictions**: HANConv architecture — trained directly per ICH E11 age band on uploaded quarterly data
- **Ablation Study**: 4-config ablation measuring cohort and co-admin edge contributions
- **7-Page Dashboard**: Upload Hub, Demographics, ADR Analysis, Signal Detection, GNN Network, Outcomes, Report Builder
- **PDF Export**: Generate structured reports with jsPDF + html2canvas

## Data Strategy

```
┌──────────────────────────────────────────────────────────────────┐
│  FAERS 2025 Q1-Q4         → GNN TRAINING + SIGNAL DETECTION      │
│    Your uploaded files      Filter to pediatric only             │
│    7 files × 4 quarters     ICH E11 age-band stratification     │
│                             PRR/ROR/IC/EBGM per age band        │
│                                                                  │
│  Research approach         → NOVEL DISCOVERIES                   │
│    Data-driven              Trained purely on user-provided data │
│    Pediatric-focused        Identifies novel pediatric signals   │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Docker Compose (Recommended)
```bash
docker-compose up -d
```
This starts PostgreSQL, Redis, Backend, Celery Worker, and Frontend.

### 2. Manual Setup (Windows / PowerShell)

**Backend (Terminal 1):**
```powershell

pip install -r requirements.txt
$env:SKIP_RXNORM="1"
$env:PYTHONIOENCODING="utf-8"
cd "E:\Adverse drugs Project 2\faers-pediatric-adr\backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Celery Worker (Terminal 2):**
```powershell
cd "E:\Adverse drugs Project 2\faers-pediatric-adr\backend"
celery -A celery_worker worker --loglevel=info
```

**Frontend (Terminal 3):**
```powershell
cd "E:\Adverse drugs Project 2\faers-pediatric-adr\frontend"
npm run dev
```

### 3. Access
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/api/health

## FAERS Data

Upload quarterly FAERS `.txt` files (DEMO, DRUG, REAC, OUTC, RPSR, THER, INDI) via the Upload Hub.

Files are `$`-delimited with header rows. The pipeline auto-detects file types from headers.

## Pipeline Enhancements (Phase 3)

| Enhancement | Description |
|------------|-------------|
| DN role cleaning | Removes `role_cod='DN'` (Definitively Not suspect) from drug analysis |
| Route normalization | Maps 'Unknown'/'Other' → NULL, normalizes variants (e.g. 'Intravenous use' → 'Intravenous') |
| INDI cleaning | Expanded unknown indication strings (4 patterns) |
| Cross-quarter dedup | `deduplicate_across_quarters()` for multi-quarter stacking |
| Age unknown flag | `age_unknown=True` when both age and age_grp are null |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/ingest` | Upload FAERS files |
| GET | `/api/upload/task/{id}` | Poll pipeline status |
| POST | `/api/upload/approve/{id}` | Commit to DB |
| GET | `/api/demographics/summary` | Population stats |
| GET | `/api/demographics/age-pyramid` | Age-sex breakdown |
| GET | `/api/signals/compute` | Signal detection results |
| POST | `/api/gnn/train/{age_group}` | Train GNN model |
| GET | `/api/gnn/predictions/{age_group}` | Novel predictions |
| GET | `/api/reports/summary` | PDF report data |

## GNN Architecture

```
Stage: Training (FAERS 2025 Pediatric)
  ┌─────────────────────────────┐
  │  HANConv Layer 1            │
  │  (4 heads, dropout=0.3)     │
  │           ↓ ELU             │
  │  HANConv Layer 2            │
  │  (1 head, dropout=0.1)      │
  │           ↓                 │
  │  Dot-product decoder        │
  └─────────────────────────────┘
  100 epochs, LR=0.001
  Per ICH E11 age band
```

## Critical Constraints

1. NEVER drop rows for NULL dates or missing age
2. Dedup by `caseid + MAX(caseversion)`
3. Signal detection uses `role_cod = 'PS'` only
4. No DB write until user clicks Approve
5. ICH E11 age bands only (no arbitrary bins)
6. GNN trains per age_group independently
7. Cross-quarter dedup at merge time (not per-file)
8. Remove `role_cod='DN'` before any drug analysis

## Project Structure

```
faers-pediatric-adr/
├── backend/
│   ├── app/
│   │   ├── pipeline/          # ETL pipeline modules
│   │   │   ├── orchestrator.py     # 11-step pipeline
│   │   │   ├── validator.py        # File type detection
│   │   │   ├── deduplicator.py     # Dedup + DN cleaning
│   │   │   ├── age_normalizer.py   # Age → years + ICH E11
│   │   │   ├── drug_normalizer.py  # RxNorm + route normalization
│   │   │   ├── pediatric_filter.py # <18 filter
│   │   │   ├── date_handler.py     # Null-safe date parsing
│   │   │   └── outcome_scorer.py   # Severity scoring
│   │   ├── analytics/         # Signal detection
│   │   │   ├── signal_engine.py    # Contingency tables + compute
│   │   │   ├── prr.py / ror.py / ic.py / ebgm.py
│   │   ├── gnn/               # Graph Neural Network
│   │   │   ├── model.py            # PediatricADRHAN (HANConv)
│   │   │   ├── graph_builder.py    # Graph building
│   │   │   ├── trainer.py          # Per-age band trainer
│   │   │   ├── ablation.py         # Ablation study
│   │   │   └── predictor.py        # Inference
│   │   └── routers/           # API endpoints
│   ├── alembic/versions/      # DB migrations
│   └── test_pipeline.py       # Integration test
├── frontend/                  # React 18 + Vite + Tailwind
│   └── src/pages/             # 7 dashboard pages
└── data/                      # FAERS quarterly files
```

## License

Research use only — PulseTech Team (ANC-031)
