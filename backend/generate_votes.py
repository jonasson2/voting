from table_util import add_totals, find_xtd_shares
from random import randint, uniform
import dictionaries

def adjustment(vote):
    return max(0.01, vote + uniform(-0.01, 0.01))

def generate_votes (
    base_votes,      # 2d - votes for each list
    var_coeff,       # coefficient of variation, SD/mean
    distribution,    # "beta", "uniform"...
    apply_random=-1, # -1: apply randomness to all constituencies
    #                # otherwise only to constituency rand_constit
):
    """
    Generate a set of random votes using 'base_votes' as reference.
    """
    rand = dictionaries.GENERATING_METHODS[distribution]
    
    # xtd_votes = add_totals(base_votes)
    # xtd_shares = find_xtd_shares(xtd_votes)

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
            if apply_randomness:
                vote = rand(mean, var_coeff)
            else:
                vote = mean
            if vote >= 1:
                vote = round(vote)
            vote = adjustment(vote)
            generated_votes[c].append(vote)

    return generated_votes

# def generate_maxchange_votes (
#     base_votes,   # 2d - votes for each list
#     max_change,   # maximum change as a fraction of total constituency votes
#     apply_random, # -1: apply randomness to all constituencies
#     #             # otherwise only to constituency rand_constit
# ):
#     """Votes of a random list are modified by a fraction max_change of the total
#     constituency votes and the remaining lists receive a smaller random change.
#     All changes are selected randomly as an increase or a decrease.
#     """
#     xtd_votes = add_totals(base_votes)
#     xtd_shares = find_xtd_shares(xtd_votes)

#     generated_votes = []
#     num_constit = len(base_votes)
#     num_parties = len(base_votes[0])
    
#     for c in range(num_constit):
#         apply_randomness = apply_random == -1 or c == apply_random
#         generated_votes.append([])
#         max_list = randint(0, num_parties-1)
#         for p in range(num_parties):
#             mean = xtd_shares[c][p]
#             assert 0 <= mean and mean <= 1
#             if mean == 0 or mean == 1 or not apply_randomness:
#                 share = mean
#             elif p == max_list:
#                 sign = randint(0,1)*2 - 1
#                 share = mean + sign*max_change
#             else:
#                 share = mean + max_change*uniform(-1,1)
#             generated_votes[c].append(max(1,round(share*xtd_votes[c][-1])))

#     return generated_votes
