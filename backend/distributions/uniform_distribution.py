from random import uniform
from math import sqrt

def uniform_distribution(mu, var_coeff):
    # The uniform distribution is parameterized with its mean and relative SD
    # (standard deviation divided by mean). 

    sigma = var_coeff*mu
    d = sqrt(3)*sigma
    a = max(0, mu - d)
    b = mu + d
    return uniform(a, b)
