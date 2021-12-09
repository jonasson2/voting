from random import gammavariate

def gamma_distribution(mu, var_coeff):
    # Parameterize with mean and coefficient of variation (standard deviation divided by mean). 
    alpha = 1/var_coeff**2
    beta = mu/alpha
    return gammavariate(alpha, beta)
