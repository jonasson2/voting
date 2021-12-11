from random import betavariate

# Symmetric beta distribution with support [0,2*mu] and specified coefficient of variation
def symmetric_beta_distribution(mu, var_coeff):
    alpha = (1/var_coeff**2 - 1)/2
    beta = alpha
    x = betavariate(alpha, beta)
    return 2*x*mu
