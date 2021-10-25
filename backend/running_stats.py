import numpy as np

class Running_stats:
    def __init__(self, shape):
        self.n = 0
        self.M1 = np.zeros(shape)
        self.M2 = np.zeros(shape)
        self.M3 = np.zeros(shape)
        self.M4 = np.zeros(shape)
        self.big = np.zeros(shape)
        self.small = np.zeros(shape)

    def update(self, A): # A should have shape "shape"
        A = np.array(A)
        self.n += 1
        n = self.n
        delta = A - self.M1
        delta_n = delta/n
        delta_n2 = delta_n**2
        term1 = delta*delta_n*n
        self.M1 += delta_n
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

    def mean(self):
        return self.M1.tolist()

    def std(self):
        n = self.n
        return np.sqrt(self.M2/max(1,n-1)).tolist()

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
# No. 348, 859-866.
#
# Donald Knuth, Art of Computer Programming, Vol 2, page 232, 3rd edition