import numpy as np
np.set_printoptions(suppress=True, floatmode="fixed", precision=3, linewidth=200)
from scipy.io import loadmat

RNG = np.random.default_rng(seed = 42)

def random_votes(nsim, partyvotes, pcv, constvotes, cv, info, model_params):
    # gcv[l] is nsim by nconst[l] by nparty
    parties = [m[0] for m in model_params['parties'][:,0]]
    kerg_parties = list(info['party'].values())
    nland = len(info['land'])
    nparty = len(parties)
    nconst = [constvotes[l].shape[0] for l in range(nland)]
    pv_means = np.zeros((nland, nparty))
    cv_means = [np.zeros((nconst[l], nparty)) for l in range(nland)]
    for q in range(nparty):
        p = parties[q]
        Q = [k in ("CDU", "CSU") if p=="CDU/CSU"
             else k in ("SSW", "other") if p=="other"
             else k == p
             for k in kerg_parties]
        pv_means[:, q] = np.sum(partyvotes[:, Q])
        for l in range(nland):
            cv_means[l][:, q] = np.sum(constvotes[l][:, Q])
    gpv = random_partyvotes(nsim, pcv, pv_means)
    gcv = random_const_votes(nsim, cv, cv_means)
    gcv = [g/g.sum(-1)[:,:,None]*100 for g in gcv]
    gpv = gpv/gpv.sum(-1)[:,:,None]*100
    return gcv, gpv

def random_partyvotes(nsim, pcv, partyvotes):
    shapep = 1/pcv**2
    scalep = 1/shapep
    sizep = (nsim,) + np.shape(partyvotes)
    gpv = RNG.gamma(shapep, scalep, size = sizep)*partyvotes
    return gpv

def random_const_votes(nsim, cv, constvotes):
    shape=1/cv**2
    scale = 1/shape
    gcv = []
    for l in range(len(constvotes)):
        size = (constvotes[l].shape[0], nsim, constvotes[l].shape[1])
        randvotes = RNG.gamma(shape, scale, size=size)*constvotes[l][:,None,:]
        gcv.append(randvotes)
    return gcv

def correlated_votes(nsim, nconst):
    model_params = loadmat("matlab/model_params.mat")
    gpv = correlated_partyvotes(nsim, model_params)
    gcv = regressed_const_votes(gpv, nconst)
    votesum = model_params["votesum"]
    parties = [m[0] for m in model_params['parties'][:,0]]
    länder = [m[0] for m in model_params['lander'][:,0]]
    [gcv, gpv] = move_CDU_CSU(gcv, gpv, parties, länder)
    gpv *= votesum[:,:,None]/100
    for l in range(16):
        gcv[l] *= votesum[0,l]/100
    return gcv, gpv

def correlated_partyvotes(nsim, model_params):
    Sig = model_params["Sig"]
    mu = model_params["mu"]
    (nland, nparty) = mu.shape
    gpv = np.zeros((nsim, nland, nparty))
    for p in range(nparty):
        X = RNG.multivariate_normal(mu[:,p], Sig[:,:,p], nsim)
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

def regressed_const_votes(partyvotes, nconst):
    data = loadmat("matlab/regression_params.mat")
    M = np.interp(partyvotes, *get_interp_points(data, "beta"))
    nland = partyvotes.shape[1]
    S = np.interp(partyvotes, *get_interp_points(data, "sigma"))
    # S = S*0.9;
    (mu, sig) = lognparam(M, S**2)
    cv = []
    for l in range(nland):
        mul = np.tile(mu[:,l,:][:,None,:], (1, nconst[l], 1))
        sigl = np.tile(sig[:,l,:][:,None,:], (1, nconst[l], 1))
        cvl = np.zeros_like(sigl)
        mask = sigl > 0
        cvl[mask] = RNG.lognormal(mul[mask], sigl[mask])
        cv.append(cvl)
    return cv

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
    import matplotlib.pyplot as plt
    import scipy.stats as st
    import json
    nsim = 99
    cv = 0.3
    pcv = 0.2
    model_params = loadmat("matlab/model_params.mat")
    gpv = correlated_partyvotes(nsim, model_params)
    [_, nland, nparty] = gpv.shape
    json = json.load(open('partyvotes.json'))
    nconst = [len(json['cv'][-1][l]) for l in range(nland)]
    gcv = regressed_const_votes(gpv, nconst)
    #[gcv, gpv] = correlated_votes(nsim)
    #partyvotes = data["partyvotes"]
    #constvotes = data["constvotes"]
    #[gcv, gpv] = random_votes(nsim, partyvotes, pcv, constvotes, cv, info, model_params)
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