from math import sqrt

import numpy as np


def adjustment(vote, rng):
    return vote + rng.unif(a=-0.01, b=0.01)


def generated_vote(mean, var_coeff, distribution, rng):
    if var_coeff == 0:
        return mean
    if distribution == "beta":
        sigma = var_coeff * mean
        alpha = ((1 - mean) / sigma**2 - 1 / mean) * mean**2
        beta = alpha * (1 / mean - 1)
        return rng.beta(a=alpha, b=beta)
    if distribution == "gamma":
        shape = 1 / var_coeff**2
        return rng.gamma(shape=shape, scale=mean / shape)
    if distribution == "uniform":
        deviation = sqrt(3) * var_coeff * mean
        return rng.unif(a=max(0, mean - deviation), b=mean + deviation)
    raise ValueError(f"Unknown vote-generating distribution: {distribution}")


def generate_votes(base_votes, var_coeff, distribution, rng):
    """
    Generate a set of random votes using 'base_votes' as reference.
    """
    generated_votes = []
    num_constit = len(base_votes)
    num_parties = len(base_votes[0])
    for c in range(num_constit):
        generated_votes.append([])
        for p in range(num_parties):
            mean = base_votes[c][p]
            if mean == 0:
                vote = 0
            else:
                vote = round(generated_vote(mean, var_coeff, distribution, rng))
            if vote >= 1:
                vote = adjustment(vote, rng)
            generated_votes[c].append(vote)
    return generated_votes

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
