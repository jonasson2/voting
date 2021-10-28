import numpy as np
import csv
from noweb import load_systems

sys_file = "11kerfi.json"
systems, _ = load_systems(sys_file)
systemnames = [s["name"] for s in systems]

def readcsv(f):
    L = []
    with open('means.dat', 'r') as f:
        reader = csv.reader(f)
        for line in reader:
            L.append([float(x) for x in line])
    return L

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
    sc = round(np.sqrt(nsys))
    sr = math.ceil(nsys/sc)
    plt.figure(figsize=(14,8))
    xmax = math.ceil(results.max())
    ylims = np.zeros(nsys)
    ax = []
    for j in range(nsys):
        rj = results[:,j]        
        axj = plt.subplot(sr, sc, j+1)
        ax.append(axj)
        plt.hist(rj, bins=xmax*10, range = (0,xmax), rwidth=0.8)
        plt.grid()
        plt.xlabel(names[j])
        plt.axvline(2, linewidth=3, color='crimson')
        ylims[j] = plt.gca().get_ylim()[1]
    ylim = max(ylims)
    for j in range(nsys): # Let all plots have same ylim:
        plt.sca(ax[j])
        plt.ylim(0, ylim)
    plt.tight_layout()
    plt.savefig('plot.png')

L = readcsv('means.dat')
print(L)
plot(L, systemnames)
