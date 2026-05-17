"""
Empirical Bayes Geometric Mean (EBGM) — simplified GPS/DuMouchel approach.
"""
import numpy as np


def compute_ebgm(ct: dict) -> dict:
    """
    Compute EBGM with EB05 (5th percentile lower bound).

    Uses standard GPS mixture priors:
    alpha1=0.2, beta1=0.06, alpha2=1.4, beta2=1.8, w=0.1

    Signal criteria: EB05 > 2
    """
    n11, n1x, nx1, nxx = ct["n11"], ct["n1x"], ct["nx1"], ct["nxx"]

    if nxx == 0 or n1x == 0 or nx1 == 0:
        return {"ebgm": None, "eb05": None}

    expected = (n1x * nx1) / nxx

    if expected == 0:
        return {"ebgm": None, "eb05": None}

    # Standard GPS mixture priors
    alpha1, beta1 = 0.2, 0.06
    alpha2, beta2 = 1.4, 1.8
    w = 0.1

    try:
        ebgm = np.exp(
            w * np.log((alpha1 + n11) / (beta1 + expected + n11))
            + (1 - w) * np.log((alpha2 + n11) / (beta2 + expected + n11))
        )

        # EB05 approximation: lower 5th percentile
        eb05 = ebgm * np.exp(-1.645 * np.sqrt(1 / (n11 + 0.5)))

        return {
            "ebgm": round(float(ebgm), 4),
            "eb05": round(float(eb05), 4),
        }
    except Exception:
        return {"ebgm": None, "eb05": None}
