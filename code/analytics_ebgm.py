"""
Empirical Bayes Geometric Mean (EBGM) — DuMouchel (1999) Multi-item
Gamma Poisson Shrinker.

Reference:
    DuMouchel W. Bayesian data mining in large frequency tables, with an
    application to the FDA spontaneous reporting system. Am Stat.
    1999;53(3):177-190.

The prior on lambda (= true RR) is a mixture of two Gamma distributions:
    pi(lambda) = w * Gamma(alpha1, beta1) + (1-w) * Gamma(alpha2, beta2)

Given observed count n = n11 and expected count E, the posterior is also
a two-component Gamma mixture with updated parameters and weights.

EBGM  = posterior mean of lambda  (the "geometric mean" name is historical)
EB05  = 5th percentile of the posterior  (lower credible bound)
"""
import numpy as np
from scipy import stats


def compute_ebgm(ct: dict) -> dict:
    """
    Compute EBGM and EB05 using the DuMouchel two-component Gamma mixture.

    Parameters
    ----------
    ct : dict with keys n11, n1x, nx1, nxx

    Returns
    -------
    dict with keys ebgm, eb05 (floats rounded to 4 dp, or None)

    Signal criterion: EB05 > 2
    """
    n11, n1x, nx1, nxx = ct["n11"], ct["n1x"], ct["nx1"], ct["nxx"]

    if nxx == 0 or n1x == 0 or nx1 == 0:
        return {"ebgm": None, "eb05": None}

    E = (n1x * nx1) / nxx  # expected count under independence

    if E == 0:
        return {"ebgm": None, "eb05": None}

    n = n11  # observed count

    # ── Prior hyperparameters (DuMouchel 1999, Table 1 defaults) ──
    alpha1, beta1 = 0.2, 0.1
    alpha2, beta2 = 2.0, 4.0
    w = 0.1  # prior mixing weight for component 1

    # ── Posterior parameters ──
    # Each component's posterior is Gamma(alpha_k + n, beta_k + E)
    a1_post = alpha1 + n
    b1_post = beta1 + E
    a2_post = alpha2 + n
    b2_post = beta2 + E

    # ── Posterior mixing weights (Bayes' rule) ──
    # log marginal likelihood for component k:
    #   log p(n | k) = a_k*log(b_k) - a_k_post*log(b_k_post)
    #                  + lgamma(a_k_post) - lgamma(a_k) - lgamma(n+1)
    # The lgamma(n+1) term cancels in the ratio, so we drop it.
    try:
        from scipy.special import gammaln

        log_m1 = (alpha1 * np.log(beta1) - a1_post * np.log(b1_post)
                  + gammaln(a1_post) - gammaln(alpha1))
        log_m2 = (alpha2 * np.log(beta2) - a2_post * np.log(b2_post)
                  + gammaln(a2_post) - gammaln(alpha2))

        # Numerically stable softmax for posterior weights
        log_w1 = np.log(w) + log_m1
        log_w2 = np.log(1 - w) + log_m2
        log_max = max(log_w1, log_w2)
        Q1 = np.exp(log_w1 - log_max) / (np.exp(log_w1 - log_max) + np.exp(log_w2 - log_max))
        Q2 = 1.0 - Q1

        # ── EBGM = posterior mean of lambda ──
        # E[lambda] = Q1 * (a1_post / b1_post) + Q2 * (a2_post / b2_post)
        ebgm = Q1 * (a1_post / b1_post) + Q2 * (a2_post / b2_post)

        # ── EB05 = 5th percentile of the posterior mixture ──
        # Solve for x such that Q1*F1(x) + Q2*F2(x) = 0.05
        # where F_k is the Gamma(a_k_post, scale=1/b_k_post) CDF
        dist1 = stats.gamma(a=a1_post, scale=1.0 / b1_post)
        dist2 = stats.gamma(a=a2_post, scale=1.0 / b2_post)

        # Binary search for the 5th percentile of the mixture
        lo, hi = 0.0, ebgm * 5.0 + 1.0
        for _ in range(80):
            mid = (lo + hi) / 2.0
            cdf_mix = Q1 * dist1.cdf(mid) + Q2 * dist2.cdf(mid)
            if cdf_mix < 0.05:
                lo = mid
            else:
                hi = mid
        eb05 = (lo + hi) / 2.0

        return {
            "ebgm": round(float(ebgm), 4),
            "eb05": round(float(eb05), 4),
        }
    except Exception:
        return {"ebgm": None, "eb05": None}

