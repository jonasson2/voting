from random import betavariate

def beta_distribution(mu, var_coeff):
    # Parameterize with mean and relative SD (standard deviation divided by mean). 
    # See: https://stats.stackexchange.com/questions/12232/calculating-the-parameters-of-a-beta-distribution-using-the-mean-and-variance
    if var_coeff == 0:
        return mu
    else:
        sigma = var_coeff*mu
        alpha = ((1 - mu)/sigma**2 - 1/mu)*mu**2
        beta = alpha*(1/mu - 1)
        lower_mean = mu if mu<=0.5 else 1-mu
        return betavariate(alpha, beta)
