from math import log, sqrt

import numpy as np


def generate_votes(base_votes, var_coeff, distribution, rng):
    """Generate continuous votes with one batch of random factors per table."""
    if distribution not in ("beta", "gamma", "log-normal", "uniform"):
        raise ValueError(f"Unknown vote-generating distribution: {distribution}")
    means = np.asarray(base_votes, dtype=float)
    if var_coeff == 0:
        return means.tolist()

    # A common relative SD lets every cell use the same factor distribution.
    if distribution == "beta":
        shape = (1 / var_coeff**2 - 1) / 2
        factors = 2 * rng.beta(size=means.shape, a=shape, b=shape)
    elif distribution == "gamma":
        shape = 1 / var_coeff**2
        factors = rng.gamma(size=means.shape, shape=shape, scale=1 / shape)
    elif distribution == "log-normal":
        sigma_squared = log(1 + var_coeff**2)
        factors = rng.lognormal(
            size=means.shape,
            mu=-sigma_squared / 2,
            sigma=sqrt(sigma_squared),
        )
    else:
        deviation = sqrt(3) * var_coeff
        factors = rng.unif(
            size=means.shape, a=max(0, 1 - deviation), b=1 + deviation)
    return (means * factors).tolist()


def generate_corr_votes(
    votes,
    const_rsd,
    const_corr,
    party_votes = [],
    party_vote_rsd = 0,
    party_vote_corr = 0,
    rng = None,
):
    if rng is None:
        raise ValueError("Correlated vote generation requires an RNG.")
    include_pv = len(party_votes) > 0
    M = np.array(votes)
    nconst, nparty = M.shape
    if include_pv:
        gv = np.zeros((nconst+1, nparty))
    else:
        gv = np.zeros((nconst, nparty))

    for p in range(nparty):
        M_p = M[:, p]
        V = (M_p*const_rsd)**2
        sigma = np.sqrt(np.log(1 + V / np.maximum(1, M_p**2)))
        mu = np.log(np.maximum(1,M_p)) - sigma ** 2 / 2
        e = np.sqrt(np.exp(sigma ** 2) - 1)

        if include_pv:
            Mpv = party_votes[p]
            Vpv = (Mpv*party_vote_rsd)**2
            sigma_pv = np.sqrt(np.log(1 + Vpv / np.maximum(1, Mpv**2)))
            mu_pv = np.log(Mpv) - sigma_pv ** 2 / 2
            e_pv = np.sqrt(np.exp(sigma_pv ** 2) - 1)
            corr = np.zeros((nconst + 1, nconst +1))
            corr[-1, -1] = 1
        else:
            corr = np.zeros((nconst, nconst))

        for i in range(nconst):
            corr[i, i] = 1
            if sigma[i] == 0:
                for j in range(i):
                    corr[i,j] = 0
                    corr[j,i] = 0
                corr[-1,i] = 0
                if include_pv:
                    corr[-1,i] = 0
                    corr[i,-1] = 0
            else:
                for j in range(i):
                    if sigma[j] == 0:
                        corr[i,j] = 0
                    else:
                        corr[i, j] = np.log(e[i]*e[j]*const_corr + 1)\
                            /(sigma[i]*sigma[j])
                    corr[j, i] = corr[i, j]
                if include_pv:
                    corr[-1, i] = np.log(e[i]*e_pv*party_vote_corr + 1)\
                        /(sigma[i]*sigma_pv)
                    corr[i, -1] = corr[-1, i]

        if include_pv:
            sigma_ext = np.append(sigma, sigma_pv)
            mu_ext = np.append(mu, mu_pv)
            Sig = sigma_ext[:,None]*corr*sigma_ext
            gv[:, p] = np.exp(rng.mvn(Sigma=Sig, mu=mu_ext)[0])

        else:
            Sig = sigma[:, None] * corr * sigma
            gv[:, p] = np.exp(rng.mvn(Sigma=Sig, mu=mu)[0])

    return (gv[:-1].tolist(), gv[-1].tolist()) if include_pv \
        else (gv.tolist(), [])
