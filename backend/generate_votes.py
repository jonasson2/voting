from table_util import add_totals, find_xtd_shares
import dictionaries

def generate_votes (
    base_votes,   # 2d - votes for each list
    var_coeff,    # coefficient of variation, SD/mean
    distribution, # "beta", "uniform"...
    apply_random, # -1: apply randomness to all constituencies
    #             # otherwise only to constituency rand_constit
):
    """
    Generate a set of random votes using 'base_votes' as reference.
    """
    rand = dictionaries.GENERATING_METHODS[distribution]
    
    xtd_votes = add_totals(base_votes)
    xtd_shares = find_xtd_shares(xtd_votes)

    generated_votes = []
    num_constit = len(base_votes)
    num_parties = len(base_votes[0])
    for c in range(num_constit):
        generated_votes.append([])
        for p in range(num_parties):
            mean = xtd_shares[c][p]
            assert 0 <= mean and mean <= 1
            if mean == 0 or mean == 1 or c == apply_random:
                share = mean
            else:
                share = rand(mean, var_coeff)
            generated_votes[c].append(int(share*xtd_votes[c][-1]))

    return generated_votes
