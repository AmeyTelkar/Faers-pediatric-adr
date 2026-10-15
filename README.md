# PulseTech: Pediatric FAERS Pharmacovigilance Dashboard with Heterogeneous GNN Signal Exploration

**Full Title:** PulseTech: Design and implementation of a human-in-the-loop web dashboard for pediatric FAERS pharmacovigilance with heterogeneous graph neural network signal exploration

**Authors:** Telkar A, Telkar A, Javalgikar A, Ruikar D, Madanwale N.

**Journal:** PLOS ONE (submitted)

<!-- After the first GitHub release is archived by Zenodo, replace every ZENODO_CONCEPT_DOI in this file (badge line and Citation section) with the concept DOI, e.g. 10.5281/zenodo.1234567 -->
[![DOI](https://zenodo.org/badge/DOI/ZENODO_CONCEPT_DOI.svg)](https://doi.org/ZENODO_CONCEPT_DOI)

---

## Overview

This repository contains the code, derived datasets, supplementary information and figures for PulseTech, a web-based pharmacovigilance dashboard for pediatric reports in the FDA Adverse Event Reporting System (FAERS), 2021Q1–2025Q4. PulseTech combines a 13-step ingestion pipeline with a mandatory human quality gate, in-dashboard four-metric disproportionality analysis (PRR, ROR, IC/BCPNN, EBGM) across ICH E11(R1) pediatric age bands, and an interactive heterogeneous graph attention network (HANConv) view for exploring drug–adverse drug reaction (ADR) relationships.

Disproportionality signals are hypothesis-generating reporting associations, not causal findings.

---

## Repository Structure

```
.
├── code/                          # Core algorithmic scripts
│   ├── graph_builder.py           # Heterogeneous drug–ADR–cohort graph construction
│   ├── model.py                   # PediatricADRHAN (HANConv) model definition
│   ├── predictor.py               # Candidate drug–ADR link ranking
│   ├── signal_engine.py           # Four-metric signal flagging
│   ├── orchestrator.py            # 13-step ingestion pipeline orchestrator
│   ├── deduplicator.py            # Case deduplication and role-code filtering
│   ├── validator.py               # FAERS quarterly file validation
│   ├── verify_signal_flags.py     # Re-checks the S8 Table flags and the 419 graph count
│   ├── verify_reported_counts.py  # Re-checks manuscript counts against dataset/ and S8 Table
│   ├── figure_sources/            # LaTeX/TikZ sources for Fig 3 and S1 Fig
│   ├── requirements.txt
│   └── README.md                  # Code documentation and reproducibility status
├── dataset/                       # Database exports used to verify the manuscript
│   └── README.md                  # What each workbook supports
├── Submission_Figures/            # Figures as submitted (TIFF / EPS) + PNG previews
├── Supplementary_Information/     # S1–S8 Tables (Excel) and S1 Fig
├── CITATION.cff
├── .zenodo.json                   # Zenodo metadata (authors, licence, keywords)
├── LICENSE
└── README.md
```

---

## Key Results

| Quantity | Value |
|---|---|
| FAERS quarters loaded | 20 (2021Q1–2025Q4) |
| Patient records | 3,420,201 |
| Records with a resolved pediatric age band | 606,334 (Neonate 23,704 · Infant 29,963 · Child 149,389 · Adolescent 403,278) |
| Records with unresolved age (kept as an explicit Unknown band) | 2,813,867 (82.27%) |
| Drug–ADR pairs evaluated, four resolved bands | 6,259 |
| Flagged signals, four resolved bands | 5,266 |
| … of which also meet the Evans criteria | 4,689 (89.0%) |
| Flagged signals, all five bands (dashboard total) | 82,650 |
| CHILD-band graph | 79 drug nodes, 259 ADR nodes, 500 edges |
| … signal edges shown in the dashboard (Fig 6) | 419 (83.8%) |
| MedDRA check | 1,381 of 1,382 adverse-event terms are current MedDRA 28.1 Preferred Terms |

**Important:** most records in the Unknown band are for predominantly adult products, so all-band figures describe the loaded data, not a pediatric population. Only results within the four resolved bands are pediatric findings.

---

## Signal Detection Criteria

A drug–ADR pair is flagged as a signal if **any** of the following is met. This is the rule that reproduces every flag in S8 Table.

| Metric | Criterion |
|---|---|
| PRR | PRR ≥ 2 (χ² is computed and reported but not required) |
| ROR | ROR ≥ 2 and 95% CI lower bound > 1 |
| IC | IC025 > 0 |
| EBGM | EB05 > 2 |

This any-method rule is more permissive than the conventional Evans criteria (PRR ≥ 2, χ² ≥ 4, n ≥ 3).

**Two forms of the rule.** `is_signal()` in `code/signal_engine.py` also requires χ² ≥ 4 for the PRR criterion. That stricter form flags the same pairs except the 269 that the stored results flag on the PRR point estimate alone (4,997 instead of 5,266), and applied to the 500 CHILD-band edges it gives the 419 signal edges shown by the dashboard's GNN Network View (Fig 6). The stored rule flags 420; the extra edge is Eligard – Weight increased (n11 = 8, PRR 2.01, χ² 3.05). `code/verify_signal_flags.py` demonstrates both.

---

## Reproducibility

| Component | Status |
|---|---|
| Signal-detection results (S8 Table) | Shipped as complete output (6,259 pairs, four resolved bands) |
| Signal flags, signal counts and the 419 graph count | Re-checked by `code/verify_signal_flags.py` (runs from this archive) |
| Counts reported in the manuscript | Re-checked by `code/verify_reported_counts.py` against `dataset/` and S8 Table; the script lists the few numbers that rest on the dashboard alone |
| Graph construction, model definition, link ranking | Code included (`code/`) |
| Fig 3 and S1 Fig | Regenerable from `code/figure_sources/` (pdflatex) |
| Figs 1, 2, 4–9 | Dashboard screenshots |
| PRR / ROR / IC / EBGM computation modules | Not included – output provided in S8 Table |
| GNN training module and five pipeline steps | Not included – see `code/README.md` |
| 2×2 contingency cells | Not included in S8 Table |

### Known issues in this version

<!-- Update or remove each item when it is resolved. -->

1. **EBGM values** in S8 Table never exceed 0.992, which is inconsistent with the DuMouchel Multi-item Gamma Poisson Shrinker. They should not be interpreted; no pair reached EB05 > 2, so EBGM contributed no flags, and EBGM is not a model input.
2. **Training parameters**: manuscript Table 5 and S4 Table both specify 100 epochs, learning rate 0.01, weight decay 1e-4, split 80/10/10, matching `app/gnn/trainer.py`.

## Running the checks

Python 3.9+ with `pandas` and `openpyxl`:

```
pip install pandas openpyxl
python code/verify_signal_flags.py
python code/verify_reported_counts.py
```

Each script prints PASS or FAIL for every number it checks and exits with status 0 only if all pass.

---

## Data Availability

- **FAERS data:** publicly available from the [U.S. FDA](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html)
- **Signal-detection output:** complete results in `Supplementary_Information/S8_Table_Complete_Signal_Detection.xlsx`
- **Verification exports:** `dataset/`
- **MedDRA:** licensed from the MSSO; no MedDRA dictionary files are redistributed

---

## Citation

> Telkar A, Telkar A, Javalgikar A, Ruikar D, Madanwale N. PulseTech: Design and implementation of a human-in-the-loop web dashboard for pediatric FAERS pharmacovigilance with heterogeneous graph neural network signal exploration. *PLOS ONE* (submitted).

**Zenodo DOI:** [ZENODO_CONCEPT_DOI](https://doi.org/ZENODO_CONCEPT_DOI)

---

## License

Creative Commons Attribution 4.0 International (CC BY 4.0). See `LICENSE`.
