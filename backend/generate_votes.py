from table_util import find_percentages
from random import randint, uniform
import dictionaries

def adjustment(vote):
    return vote + uniform(-0.01, 0.01)

def generate_votes (
    base_votes,      # 2d - votes for each list
    var_coeff,       # relative SD, SD/mean
    distribution,    # "beta", "uniform"...
    apply_random=-1, # -1: apply randomness to all constituencies
    #                # otherwise only to constituency rand_constit
):
    """
    Generate a set of random votes using 'base_votes' as reference.
    """
    rand = dictionaries.GENERATING_METHODS[distribution]
    
    generated_votes = []
    num_constit = len(base_votes)
    num_parties = len(base_votes[0])
    for c in range(num_constit):
        generated_votes.append([])
        apply_randomness = apply_random == -1 or c == apply_random
        for p in range(num_parties):
            # mean = xtd_shares[c][p]
            mean = base_votes[c][p]
            # assert 0 <= mean and mean <= 1
            if mean <= 1e-6:
                vote = mean
            elif apply_randomness:
                vote = max(1, round(rand(mean, var_coeff)))
            else:
                vote = mean
            if vote >= 1:
                vote = adjustment(vote)
            generated_votes[c].append(vote)

    return generated_votes
