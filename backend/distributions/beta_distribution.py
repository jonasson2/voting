
from random import betavariate

from table_util import add_totals, find_xtd_shares


def beta_distribution(
    base_votes, #2d - votes for each list,
    var_coeff,  #coefficient of variation, SD/mean
):
    """
    Generate a set of votes with beta distribution,
    using 'base_votes' as reference.
    """

    xtd_votes = add_totals(base_votes)
    xtd_shares = find_xtd_shares(xtd_votes)

    generated_votes = []
    for c in range(len(base_votes)):
        s = 0
        generated_votes.append([])
        for p in range(len(base_votes[c])):
            mean_beta_distr = xtd_shares[c][p]
            assert 0 <= mean_beta_distr and mean_beta_distr <= 1
            if 0 < mean_beta_distr and mean_beta_distr < 1:
                alpha, beta = beta_params(mean_beta_distr, var_coeff)
                share = betavariate(alpha, beta)
            else:
                share = mean_beta_distr #either 0 or 1
            generated_votes[c].append(int(share*xtd_votes[c][-1]))

    return generated_votes

def beta_params(mu, var_coeff): # was variance_coefficient):
    # The beta distribution is parameterized with its mean and coefficient of variation
    # (standard deviation divided by mean). 

    # See: https://stats.stackexchange.com/questions/12232/calculating-the-parameters-of-a-beta-distribution-using-the-mean-and-variance
    
    assert 0<mu and mu<1
    sigma = var_coeff*mu
    alpha = ((1 - mu)/sigma**2 - 1/mu)*mu**2
    beta = alpha*(1/mu - 1)

    #make sure alpha and beta > 1 to ensure nice probability distribution
    lower_mean = mu if mu<=0.5 else 1-mu
    assert 0<lower_mean and lower_mean<=0.5
    
    assert alpha>1
    assert beta>1
    return alpha, beta
