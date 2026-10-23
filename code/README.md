# code/ — PulseTech backend source

Backend source of the PulseTech dashboard: the 13-step ingestion pipeline, the four disproportionality statistics, signal flagging, graph construction, the PediatricADRHAN (HANConv) model, its training and link ranking. Each file was taken from the `app/` package of the full system; the original module path is given in its first line. Imports try the `app.*` package path first and fall back to the flat file names used here.

| File | Purpose | Runs from this archive? |
|---|---|---|
| `orchestrator.py` | 13-step ingestion pipeline (manuscript Table 4) | No — needs FAERS quarterly files and PostgreSQL |
| `validator.py` | Step 0: file-type detection and schema validation | Library functions |
| `deduplicator.py` | Step 2: case deduplication; cross-quarter deduplication; drug role-code cleaning | Library functions |
| `pipeline_age_normalizer.py` | Steps 3–4: age units to decimal years; ICH E11(R1) bands | Library functions |
| `pipeline_pediatric_filter.py` | Step 6: age filter (Step 8, the primary-ID restriction, is in `orchestrator.py`) | Library functions |
| `pipeline_date_handler.py` | Step 7: dates to ISO 8601 | Library functions |
| `pipeline_drug_normalizer.py` | Step 10: RxNorm normalisation (API, fuzzy fallback) | Needs the RxNorm API |
| `pipeline_outcome_scorer.py` | Step 11: ordinal outcome severity | Library functions |
| `analytics_prr.py` | PRR, Woolf 95% CI, Yates-corrected χ² | Library function |
| `analytics_ror.py` | ROR and 95% CI | Library function |
| `analytics_ic.py` | IC = log2((n11 + 0.5)/(E + 0.5)) and IC025 | Library function |
| `analytics_ebgm.py` | EBGM (geometric mean of the posterior) and EB05; `fit_prior()` estimates the five MGPS hyperparameters per age band | Library function; needs scipy |
| `test_ebgm.py` | Checks `analytics_ebgm.py` against numerical integration, MGPS behaviour and prior recovery on simulated data | **Yes** — numpy, scipy |
| `signal_engine.py` | Builds 2×2 tables per age band, fits the EBGM prior for the band, and applies `is_signal()` | Needs the pipeline output |
| `graph_builder.py` | Heterogeneous drug–ADR–cohort graph | Needs torch_geometric and the pipeline output |
| `model.py` | PediatricADRHAN: two HANConv layers and a dot-product decoder | Defines the model |
| `gnn_trainer.py` | Training: 100 epochs, Adam, learning rate 0.01, weight decay 1e-4, 80/10/10 edge split, validation ROC-AUC every 5 epochs | Needs the pipeline output |
| `gnn_ablation.py` | Ablation of graph components (not used for any reported result) | Needs `gnn_trainer.py` |
| `predictor.py` | Ranks candidate drug–ADR links with a trained model | Needs a trained model |
| `config.py`, `database.py` | Settings and database sessions; every secret is read from a local `.env` (template: `.env.example`) | — |
| `verify_statistics.py` | Recomputes every PRR, χ², ROR, IC, IC025, EBGM and EB05 in S8 Table from its counts and checks the Signal flag | **Yes** — pandas, openpyxl, numpy, scipy |
| `verify_signal_flags.py` | Reproduces the S8 Table Signal flags (6,259/6,259), the counts 5,266 / 4,689 / 269, and the 419 CHILD-band signal edges | **Yes** — pandas, openpyxl |
| `verify_reported_counts.py` | Checks the counts reported in the manuscript against `../dataset/` and S8 Table | **Yes** — pandas, openpyxl |
| `figure_sources/` | LaTeX/TikZ sources of Fig 3 (model) and S1 Fig (system) | **Yes** — `pdflatex <file>.tex` |
| `requirements.txt` | Python dependencies | — |

Not included: the dashboard front end and the web API layer (the GNN Network View, including its top-500 edge selection), and the PostgreSQL database itself.

## Installing

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip
cp .env.example .env                            # then fill in the database URL and secrets
```

Python 3.11+ and PostgreSQL 15+ are needed for the backend. The four check scripts need only pandas, openpyxl, numpy and scipy and run from this archive alone:

```
python code/verify_statistics.py
python code/verify_signal_flags.py
python code/verify_reported_counts.py
python code/test_ebgm.py
```

## Model

`model.py` defines PediatricADRHAN:

- node types `drug`, `adr`, `cohort` (ICH E11 age band), each with one-hot identity features
- edge types `drug–reported_with–adr` (and reverse), `cohort–received–drug`, `cohort–experienced–adr`, optional `drug–co_administered–drug`
- layer 1: HANConv, 4 attention heads, dropout 0.3, ELU; layer 2: HANConv, 1 head, dropout 0.1
- hidden 64, output 32 (`gnn_trainer.py` defaults)
- link scoring: sigmoid of the dot product of drug and ADR embeddings

## Signal rule

A drug–ADR pair (n11 ≥ 3) is flagged if any criterion is met. This rule reproduces the stored Signal flag for all 6,259 pairs in S8 Table:

- PRR ≥ 2 (χ² is computed and reported but not required)
- ROR ≥ 2 and 95% CI lower bound > 1
- IC025 > 0
- EB05 > 2

`is_signal()` in `signal_engine.py` is a stricter form: it also requires χ² ≥ 4 for the PRR criterion. It flags the same pairs except the 269 that the stored results flag on the PRR point estimate alone (4,997 instead of 5,266). Applied to the 500 CHILD-band edges it gives the 419 signal edges shown by the dashboard's GNN Network View (Fig 6), against 420 under the stored rule; the extra edge is Eligard – Weight increased (n11 = 8, PRR 2.01, χ² 3.05). `verify_signal_flags.py` reads `is_signal()` from `signal_engine.py` unchanged and shows both results.

## Known issues

1. **EBGM prior** — only pairs with n11 ≥ 3 are stored, so `fit_prior()` works on a truncated sample and, for all four bands of the Q1 2025 cache, converges to an almost single-component prior. The EBGM values in S8 Table were regenerated with this module and are reproduced by `verify_statistics.py`. EBGM is not a model input.
2. **Versions** — package versions used in the study were not recorded; `requirements.txt` lists names only.
