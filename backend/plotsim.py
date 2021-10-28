def plot(results, names):
    # Plot an arrray of histograms of results, one for each electoral system.
    # Each histogram describes the distribution of the n_reps dev_ref average
    # values and each such value is the average over the n_betasim*n_unifsim
    # simulated election results. Can also histogram standard deviations,
    # and then each value is the average of n_betasim standard deviations.
    import matplotlib.pyplot as plt
    import math
    results = np.array(results)
    plt.rc('savefig',bbox='tight')
    (nreps, nsys) = np.shape(results)
    sr = round(np.sqrt(nsys))
    sc = math.ceil(nsys/sr)
    plt.figure(figsize=(10,8))
    xmax = math.ceil(results.max())
    ylims = np.zeros(nsys)
    ax = []
    for j in range(nsys):
        rj = results[:,j]        
        axj = plt.subplot(sr, sc, j+1)
        ax.append(axj)
        plt.hist(rj, bins=xmax, range = (0,xmax), rwidth=0.8)
        plt.xlabel(names[j])
        ylims[j] = plt.gca().get_ylim()[1]
    ylim = max(ylims)
    for j in range(nsys): # Let all plots have same ylim:
        plt.sca(ax[j])
        plt.ylim(0, ylim)
    plt.tight_layout()
    plt.savefig('plot.png')
