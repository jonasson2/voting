import numpy as np
from numpy import r_
from copy import deepcopy
from util import disp

class Running_stats:
    def __init__(self, shape=1, parallel=False, name="", options=None):
        # Names may be a list of length shape. When shape is not two-dimensional,
        self.parallel = parallel
        self.name = name
        self.options = ([] if options is None
                        else ['min', 'max', 'sum', 'avg'] if options=='all'
                        else options)
        if isinstance(shape, (tuple, list)):
            nr = shape[0] + len(self.options)
            nc = shape[1] + len(self.options)
            self.shape = (nr, nc)
        else:
            self.shape = shape + len(self.options)
        self.n = 0
        self.M1 = np.zeros(self.shape)
        self.M2 = np.zeros(self.shape)
        if not self.parallel:
            self.M3 = np.zeros(self.shape)
            self.M4 = np.zeros(self.shape)
        self.big = np.zeros(self.shape)
        self.small = np.zeros(self.shape)

    def __repr__(self):
        s = [f"Running_stats:",
             f"   n: {self.n}",
             f"   name: {self.name}",
             f"   shape: {self.shape}",
             f"   {wrap('mean:', self.mean(), 3)}",
             f"   {wrap('std: ', self.std(), 3)}",
             f"   {wrap('error: ', self.std(), 3)}"]
        r = '\n'.join(s)
        return r

    @classmethod
    def from_dict(cls,dictionary):
        self = cls()
        for (key,val) in dictionary.items():
            setattr(self, key, val)
        return self

    @classmethod
    def optfun(cls, o):
        return (np.min if o=="min"
                else np.max if o=="max"
                else np.sum if o=="sum"
                else np.mean if o=="mean" or o=="avg"
                else None)

    def extend(self, A):
        A = np.array(A)
        optfuns = [self.optfun(o) for o in self.options]
        if len(self.options) == 0:
            return A
        elif not isinstance(self.shape, tuple):
            B = np.hstack([fun(A,0) for fun in optfuns])
            return np.r_[A, B]
        else:
            B = np.vstack([fun(A,0) for fun in optfuns])
            AB = np.vstack((A, B))
            C = np.vstack([fun(AB,1) for fun in optfuns])
            ABC = np.c_[AB, C.T]
            return ABC

    def update(self, values): # values should have shape "shape"
        if type(values) in {int,float,np.float64,np.int64}:
            values = [values]
        A = self.extend(values)
        n1 = self.n
        self.n += 1
        n = self.n
        if len(A) != len(self.M1):
            pass
        delta = A - self.M1
        delta_n = delta/n
        term1 = delta*delta_n*n1
        self.M1 += delta_n
        if not self.parallel:
            delta_n2 = delta_n**2
            self.M4 += (term1 * delta_n2 * (n*n - 3*n + 3) +
                        6 * delta_n2 * self.M2 - 4 * delta_n * self.M3)
            self.M3 += term1 * delta_n * (n - 2) - 3 * delta_n * self.M2
        self.M2 += term1
        if n == 1:
            self.big = A
            self.small = A
        else:
            self.big = np.maximum(self.big, A)
            self.small = np.minimum(self.small, A)

    def combine(self, running_stats):
        n1 = self.n
        n2 = running_stats.n
        self.n = n1 + n2
        delta = running_stats.M1 - self.M1
        if self.n==0:
            print(f"**** zero n for {self.name} in running_stats combine ****")
        self.M1 = (n1*self.M1 + n2*running_stats.M1)/max(1,self.n)
        self.M2 += running_stats.M2 + delta**2*n1*n2/max(1,self.n)
        self.big = np.maximum(self.big, running_stats.big)
        self.small = np.minimum(self.small, running_stats.small)

    def mean(self):
        return self.M1.tolist()

    def numpy_mean(self):
        return self.M1

    def numpy_std(self):
        n = self.n
        var = self.M2/max(1,n-1)
        return np.sqrt(var)

    def std(self):
        return self.numpy_std().tolist()

    def error(self):
        return self.numpy_error().tolist()

    def numpy_error(self):
        n = self.n
        var = self.M2/max(1,n-1)
        return 2*np.sqrt(var/max(1,n))

    def lo95ci(self):
        n = self.n
        var = self.M2/max(1,n-1)
        return (self.M1 - 2*np.sqrt(var/max(1,n))).tolist()

    def hi95ci(self):
        n = self.n
        var = self.M2/max(1,n-1)
        return (self.M1 + 2*np.sqrt(var/max(1,n))).tolist()

    def skewness(self):
        n = self.n
        return (np.sqrt(n)*self.M3/np.maximum(1,self.M2**1.5)).tolist()

    def kurtosis(self):
        n = self.n
        return (n*self.M4/np.maximum(1,self.M2**2) - 3).tolist()

    def maximum(self):
        return self.big.tolist()

    def minimum(self):
        return self.small.tolist()

def combine_stat(stat1, stat2):
    # stat1 and stat2 are Running_stats or dictionaries of Running_stats with same keys
    # or (recursively) dictionaries of dictionaries of running_stats etc.
    # Each dictionary entry of stat1 is combined with the corresponding entry of stat2.
    if isinstance(stat1, Running_stats):
        assert(isinstance(stat2, Running_stats))
        stat1.combine(stat2)
    else:
        for (key1,key2) in zip(stat1,stat2):
            assert(key1==key2)
            combine_stat(stat1[key1], stat2[key2])

def wrap(name, L, skip=0):
    from textwrap import TextWrapper as wrapper
    if isinstance(L[0], (float,int)):
        s = "[" + ', '.join(f"{l:.2f}" for l in L) + "]"
    elif isinstance(L[0][0], (float,int)):
        s = 'Fylki'
    else:
        s = 'Óþekkt'
    tw = wrapper()
    tw.initial_indent = name + ' '
    tw.subsequent_indent = ' ' * (len(name) + 2 + skip)
    tw.width = 100
    return tw.fill(s)

    
# References:
#
# https://www.johndcook.com/blog/skewness_kurtosis/
#
# Welford, B. P. (1962). "Note on a method for calculating corrected sums of
# squares and products". Technometrics. 4 (3): 419–420. doi:10.2307/1266577.
# JSTOR 1266577.
#    
# Chan, Tony F.; Golub, Gene H.; LeVeque, Randall J. (1983). Algorithms for
# Computing the Sample Variance: Analysis and Recommendations. The American
# Statistician 37, 242-247.
#
# Ling, Robert F. (1974). Comparison of Several Algorithms for Computing Sample
# Means and Variances. Journal of the American Statistical Association, Vol. 69,
# No. 348, 85866.
#
# Donald Knuth, Art of Computer Programming, Vol 2, page 232, 3rd edition
