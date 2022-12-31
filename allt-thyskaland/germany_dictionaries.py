import sys
sys.path.append('../backend')
sys.path.append('../backend/methods')
from nearest_to_previous import nearest_to_previous
from switching import switching
#from relative_superiority import relative_superiority
from max_const_seat_share import max_const_seat_share
from common_methods import \
    max_const_vote_percentage, \
    nearest_to_previous, \
    max_const_seat_share, \
    relative_superiority, \
    rel_sup_medium, \
    rel_sup_simple
# from max_vote_percentage import max_vote_percentage
from switching import switching
from alternating_scaling import alt_scaling
from alternating_scaling import alt_scaling_new
from farthest_from_next import farthest_from_next
from max_absolute_margin import max_absolute_margin
from gurobi_optimal import gurobi_optimal
from germany_methods import parties_first, länder_first, votepct_const, rel_margin_const, \
    abs_margin_const, scandinavian, optimal_const, gurobi_optimal_const, \
    pulp_optimal_const
from method_abbrev import method_dicts_land
from dictionaries import ADJUSTMENT_METHODS

fmt = '.1f'
pct = '.1%'
nland = 16,
nparty = 9

method_dicts_const = [
    #{'short': 'scandC',   'fun': scandinavian, 'title': "Scandinavian"},
    {'short': 'votepctC', 'fun': votepct_const, 'title': "Max vote percentage"},
    {'short': 'absmargC','fun': abs_margin_const, 'title': "Max absolute margin"},
    #{'short': 'relmargC', 'fun': rel_margin_const, 'title': "Max relative margin"},
    {'short': 'optimalC', 'fun': pulp_optimal_const, 'title': "Optimal"},
    #{'short': 'pulpC',    'fun': pulp_optimal_const, 'title': "Optimal w/PuLP"}
    #{'short': 'gurobiC',  'fun': gurobi_optimal_const, 'title': "Optimal w/Gurobi"}
]

use = ['party1st', 'votepct', 'absmarg', 'relmarg', 'relsup', 'relsupmed', 'optimal']
extra = {'party1st': parties_first, 'land1st': länder_first}
land_funs = {m['short']: (ADJUSTMENT_METHODS[m['long']] if m['long'] in ADJUSTMENT_METHODS
                          else extra[m['short']])
             for m in method_dicts_land}

method_funs_const = {cm['short']: cm['fun'] for cm in method_dicts_const}
method_funs_land = land_funs

all_const_methods = [cm['short'] for cm in method_dicts_const]
all_land_methods = [lm['short'] for lm in method_dicts_land if lm['short'] in use]

land_stats = {
    'land': [
        'land_dispar',
        'land_alloc',
    ],
    'const': [
    ],
    'pairs': [
        'min_seat_share',
        'max_neg_marg',
        'neg_marg_count',
        'const_opt_diff',
        'const_entropy_diff',
    ],
}

party_stats = [
    'party_dispar',
    'party_alloc',
    'seats_minus_shares',
    'opt_diff',
]

scalar_stats = [
    'entropy_diff',
    'failure_rate',
    'total_land_disparity',
]

method_measures = [
    *scalar_stats,
    'opt_diff',
    'seats_minus_shares',
    'land_dispar',
    'party_dispar'
]

by_land = land_stats['land'] + land_stats['pairs']
by_party = party_stats

land_abbrev = {
 0: 'Sch-Hol',
 1: 'Hamb',
 2: 'N-Sachs',
 3: 'Bremen',
 4: 'NRh-Wes',
 5: 'Hessen',
 6: 'Rhl-Pfz',
 7: 'Bad-Wür',
 8: 'Bayern',
 9: 'Saarl',
 10: 'Berlin',
 11: 'Brand',
 12: 'Mec-Vor',
 13: 'Sachs',
 14: 'Sac-Anh',
 15: 'Thür'
}

def column_table(items, ncol):
    indent = " "*3
    w = max(len(i) for i in items)
    nlines = (len(items) - 1) // ncol + 1
    rows = ["  ".join([f"{c:{w}}" for c in items[i:-1:nlines]]) for i in range(nlines)]
    s = f"\n{indent}".join(rows)
    return "\n" + indent + s

land_method_table = column_table(all_land_methods, 4)
const_method_table = column_table([m[:-1] for m in all_const_methods], 4)
