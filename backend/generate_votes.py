from table_util import find_percentages
from random import randint, uniform
import dictionaries

def adjustment(vote):
    return vote + uniform(-0.01, 0.01)

def generate_votes (
    base_votes,      # 2d - votes for each list
    var_coeff,       # relative SD, SD/mean
    distribution,    # "beta", "uniform"...
):
    """
    Generate a set of random votes using 'base_votes' as reference.
    """
    rand = dictionaries.GENERATING_METHODS[distribution]
    
    generated_votes = []
    num_constit = len(base_votes)
    num_parties = len(base_votes[0])
    for c in range(num_constit):
        generated_votes.append([])
        for p in range(num_parties):
            # mean = xtd_shares[c][p]
            mean = base_votes[c][p]
            # assert 0 <= mean and mean <= 1
            if mean <= 1e-6:
                vote = mean
            vote = max(1, round(rand(mean, var_coeff)))
            if vote >= 1:
                vote = adjustment(vote)
            generated_votes[c].append(vote)

    return generated_votes

def generate_corr_votes(
    votes,
    const_rsd,
    const_corr,
    party_votes = [],
    party_vote_rsd = 0,
    party_vote_corr = 0
):
    import numpy as np
    include_pv = len(party_votes) > 0
    rng = np.random.default_rng()
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
            sigma_pv = np.sqrt(np.log(1 + Vpv / np.maximum|(1, Mpv**2)))
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
            X = rng.multivariate_normal(mu_ext, Sig)
            gv[:, p] = np.exp(X)

        else:
            Sig = sigma[:, None] * corr * sigma
            X = rng.multivariate_normal(mu, Sig)
            gv[:, p] = np.exp(X)

    return (gv[:-1].tolist(), gv[-1].tolist()) if include_pv \
        else (gv.tolist(), [])
