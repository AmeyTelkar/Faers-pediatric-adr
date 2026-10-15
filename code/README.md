# code/ — PulseTech PediatricADRHAN core scripts

These are the core algorithmic scripts of the PulseTech system, extracted from the full codebase for review and verification.

| File | Purpose | Runs from this archive? |
|---|---|---|
| `graph_builder.py` | Builds the heterogeneous drug-ADR-cohort graph from FAERS data | No - needs the PostgreSQL database |
| `model.py` | PediatricADRHAN model: two HANConv layers and a dot-product link decoder | Defines the model; needs torch and torch_geometric |
| `gnn_trainer.py` | GNN training loop: 100 epochs, Adam, LR 0.01, weight decay 1e-4, 80/10/10 split | No - needs database and model |
| `gnn_ablation.py` | Ablation study for model architecture comparison | No - needs gnn_trainer |
| `predictor.py` | Ranks candidate drug-ADR links with a trained model | No - needs trained model |
| `signal_engine.py` | Four-metric signal flagging (PRR, ROR, IC/BCPNN, EBGM) | No - needs analytics modules |
| `analytics_prr.py` | Proportional Reporting Ratio computation | Library function |
| `analytics_ror.py` | Reporting Odds Ratio computation | Library function |
| `analytics_ic.py` | Information Component (BCPNN) computation | Library function |
| `analytics_ebgm.py` | Empirical Bayes Geometric Mean computation (known defect) | Library function |
| `orchestrator.py` | 13-step ingestion pipeline (ingestion to human quality gate) | No - needs pipeline modules and database |
| `pipeline_age_normalizer.py` | Step 3: converts age units to decimal years, assigns ICH E11 bands | Library function |
| `pipeline_pediatric_filter.py` | Step 6/8: age filter and pediatric PID restriction | Library function |
| `pipeline_drug_normalizer.py` | Step 10: RxNorm drug name normalisation (API + fuzzy fallback) | Library function (needs RxNorm API) |
| `pipeline_date_handler.py` | Step 7: date normalisation to ISO 8601 | Library function |
| `pipeline_outcome_scorer.py` | Step 11: ordinal severity scoring | Library function |
| `deduplicator.py` | Step 2: case deduplication and role-code filtering | Library function |
| `validator.py` | Step 0: schema validation of FAERS quarterly files | Library function |
| `database.py` | SQLAlchemy database session factory | Config - uses environment variables |
| `config.py` | Application configuration (env-var based) | Config - uses environment variables |
| `verify_signal_flags.py` | Reproduces the S8 Table Signal flags (6,259/6,259) | Yes - needs pandas, openpyxl |
| `verify_reported_counts.py` | Checks manuscript counts against dataset/ and S8 Table | Yes - needs pandas, openpyxl |
| `figure_sources/` | LaTeX/TikZ sources of Fig 3 (model) and S1 Fig (system) | Yes - pdflatex |
| `requirements.txt` | Python dependencies | - |

No absolute file paths, hosts or credentials are hard-coded in these scripts.

## Reproducibility status

All core modules of the PulseTech system are now included in this archive. The pipeline can be traced end to end from raw FAERS files through the 13-step ingestion pipeline, disproportionality analysis, and GNN training/prediction.

### Known issues in this version

1. **EBGM** - the stored EBGM values never exceed 0.992 across 6,259 pairs. `analytics_ebgm.py` (now included) needs review. EBGM is not a model input.
