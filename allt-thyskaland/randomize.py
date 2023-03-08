import numpy as np
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from scipy.io import loadmat

def random_votes(nsim, partyvotes, prsd, constvotes, rsd, data_parties, rng):
    model_params = loadmat("matlab/model_params.mat")
    parties = [m[0] for m in model_params['parties'][:,0]]
    länder = [m[0] for m in model_params['lander'][:,0]]
    nland = len(länder)
    nparty = len(parties)
    nconst = [constvotes[l].shape[0] for l in range(nland)]
    pv_means = np.zeros((nland, nparty))
    cv_means = [np.zeros((nconst[l], nparty)) for l in range(nland)]
    for p in range(nparty):
        for l in range(nland):
            party = parties[p]
            if party == 'CDU/CSU':
                party = 'CSU' if länder[l] == 'Bayern' else 'CDU'
            q = data_parties.index(party)
            pv_means[l, p] = partyvotes[l, q]
            cv_means[l][:, p] = np.sum(constvotes[l][:, q])
    gpv = random_partyvotes(nsim, prsd, pv_means, rng)
    gcv = random_const_votes(nsim, rsd, cv_means, rng)
    [gcv, gpv] = move_CDU_CSU(gcv, gpv, parties, länder)
    return gcv, gpv

def random_partyvotes(nsim, prsd, partyvotes, rng):
    shapep = 1/prsd**2
    scalep = 1/shapep
    sizep = (nsim,) + np.shape(partyvotes)
    gpv = rng.gamma(shapep, scalep, size = sizep)*partyvotes
    return gpv

def random_const_votes(nsim, nconst, nparty, const_vote_params, param, rng):
    rsd = param['rsd']
    gcv = []
    party_votes = np.squeeze(const_vote_params['votes_all'])
    for (l, num_const) in enumerate(nconst):
        size = (nsim, num_const, nparty)
        M = np.ones(size)
        S = param['rsd']*M
        (mu, sig) = lognparam(M, S**2)
        cvl = rng.lognormal(mu, sig)
        cvl *= party_votes[l]/nconst[l]
        gcv.append(cvl)
    return gcv

def regressed_const_votes(partyvotes, nconst, rng, data):
    M = np.interp(partyvotes, *get_interp_points(data, "beta"))
    nland = partyvotes.shape[1]
    S = np.interp(partyvotes, *get_interp_points(data, "sigma"))
    (mu, sig) = lognparam(M, S**2)
    cv = []
    for l in range(nland):
        mul = np.tile(mu[:,l,:][:,None,:], (1, nconst[l], 1))
        sigl = np.tile(sig[:,l,:][:,None,:], (1, nconst[l], 1))
        cvl = np.zeros_like(sigl)
        mask = sigl > 0
        cvl[mask] = rng.lognormal(mul[mask], sigl[mask])
        cv.append(cvl)
    return cv

def generate_votes(nsim, nconst, rng, param):
    model_params = loadmat("matlab/model_params.mat")
    nparty = len(model_params['parties'])
    if param['uncorr']:
        mu = model_params['mu']
        RSD = param['prsd']
        gpv = uncorrelated_partyvotes(nsim, mu, RSD, rng)
    else:
        gpv = correlated_partyvotes(nsim, model_params, rng)
    const_vote_params = loadmat("matlab/regression_params.mat")
    if param['uncorr']:
        gcv = random_const_votes(nsim, nconst, nparty, const_vote_params, param, rng)
    else:
        gcv = regressed_const_votes(gpv, nconst, rng, const_vote_params)
    votesum = model_params["votesum"].flatten()
    parties = [m[0] for m in model_params['parties'][:,0]]
    länder = [m[0] for m in model_params['lander'][:,0]]
    [gcv, gpv] = move_CDU_CSU(gcv, gpv, parties, länder)
    gpv *= votesum[None,:,None]/100
    for l in range(16):
        gcv[l] *= votesum[l]/100/nconst[l]
    return gcv, gpv

def uncorrelated_partyvotes(nsim, mu, RSD, rng):
    sig = np.sqrt(np.log(1 + RSD**2))
    (nland, nparty) = mu.shape
    gpv = np.zeros((nsim, nland, nparty))
    for p in range(nparty):
        for l in range(nland):
            gpv[:,l,p] = rng.lognormal(mu[l,p], sig, nsim)
    return gpv

def correlated_partyvotes(nsim, model_params, rng):
    Sig = model_params["Sig"]
    mu = model_params["mu"]
    (nland, nparty) = mu.shape
    gpv = np.zeros((nsim, nland, nparty))
    for p in range(nparty):
        X = rng.multivariate_normal(mu[:,p], Sig[:,:,p], nsim)
        gpv[:,:,p] = np.exp(X)
    return gpv

def move_CDU_CSU(gcv, gpv, parties, länder):
    cdu_idx = parties.index('CDU' if 'CDU' in parties else 'CDU/CSU')
    csu_idx = cdu_idx + 1
    bayern_idx = länder.index('Bayern')

    def insert0(votes, idx):
        votes = np.insert(votes, idx, 0.0, axis=-1)
        return votes

    gpv = insert0(gpv, csu_idx)
    for l in range(len(länder)):
        gcv[l] = insert0(gcv[l], csu_idx)
    MANY = np.ndim(gpv) > 2
    if MANY:
        gpv[:, bayern_idx, csu_idx] = gpv[:, bayern_idx, cdu_idx]
        gpv[:, bayern_idx, cdu_idx] = 0.0
        gcv[bayern_idx][:, :, csu_idx] = gcv[bayern_idx][:, :, cdu_idx]
        gcv[bayern_idx][:, :, cdu_idx] = 0.0
    else:
        gpv[bayern_idx, csu_idx] = gpv[bayern_idx, cdu_idx]
        gpv[bayern_idx, cdu_idx] = 0.0
        gcv[bayern_idx][:, csu_idx] = gcv[bayern_idx][:, cdu_idx]
        gcv[bayern_idx][:, cdu_idx] = 0.0
    return gcv, gpv

def lognparam(M, V):
  # Return parameters of lognormal distribution with mean M and variance V.
  mask = M > 0
  mu = np.zeros_like(M)
  sig2 = np.zeros_like(M)
  sig = np.zeros_like(M)
  sig2[mask] = np.log(1 + V[mask]/M[mask]**2)
  mu[mask] = np.log(M[mask]) - sig2[mask]/2
  sig[mask] = np.sqrt(sig2[mask])
  return (mu, sig)

def get_interp_points(data, name):
    xp = data[name + "_breaks"].flatten()
    yp = data[name + "_values"].flatten()
    return (xp, yp)

if __name__ == "__main__":
    # tests only correlated votes
    import matplotlib.pyplot as plt
    import scipy.stats as st
    import json
    nsim = 99
    model_params = loadmat("matlab/model_params.mat")
    rng = np.random.default_rng(42)
    gpv = correlated_partyvotes(nsim, model_params, rng)
    [_, nland, nparty] = gpv.shape
    json = json.load(open('partyvotes.json'))
    nconst = [len(json['cv'][-1][l]) for l in range(nland)]
    gcv = regressed_const_votes(gpv, nconst, rng)
    plt.figure(figsize=(10,8))
    corr = np.zeros((nland, nparty))
    for l in range(nland):
        pvl = gpv[:,l,:]
        cvl = gcv[l]
        nconst = cvl.shape[1]
        partyvotes = np.tile(pvl[:, None, :], (1, nconst, 1)).flatten()
        colors = model_params["colors"]
        colors = np.tile(colors[None, None, :, :], (nsim, nconst, 1, 1)).reshape(-1,3)
        plt.scatter(partyvotes, cvl.flatten(), s=1, c=colors)
        for p in range(nparty):
            corrlist = [st.pearsonr(pvl[:,p], cvl[:,c,p])[0] for c in range(nconst)]
            corr[l,p] = sum(corrlist)/nconst
    plt.show()
    [gcv, gpv] = move_CDU_CSU(gcv, gpv, model_params)
    print(f"Simulated partyvote-constvote correlation = {corr.mean():.2f}")
    pass
