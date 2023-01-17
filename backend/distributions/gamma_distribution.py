from random import gammavariate

def gamma_distribution(mu, var_coeff):
    # Parameterize with mean and relative SD (standard deviation divided by mean).
    if var_coeff == 0:
        return mu
    else:
        alpha = 1/var_coeff**2
        beta = mu/alpha
        return gammavariate(alpha, beta)
