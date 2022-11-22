import sys
sys.path.append('../backend')
sys.path.append('../backend/methods')
from nearest_to_previous import nearest_to_previous
from switching import switching
from relative_superiority import relative_superiority
#from rel_sup import rel_sup
from max_const_seat_share import max_const_seat_share
from specified_col_sums_methods import \
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
from germany_methods import parties_first, länder_first, max_share, max_relative_margin, \
    abs_margin_const, scandinavian, optimal_const, gurobi_optimal_const
from method_abbrevs import method_dicts_land

fmt = '.1f'
pct = '.1%'
nland = 16,
nparty = 9

method_dicts_const = [
    {'short': 'scandC',   'fun': scandinavian, 'title': "Scandinavian"},
    {'short': 'votepctC', 'fun': max_share, 'title': "Max vote percentage"},
    {'short': 'relmargC', 'fun': max_relative_margin, 'title': "Max relative margin"},
    {'short': 'absmargC', 'fun': abs_margin_const, 'title': "Max absolute margin"},
    {'short': 'optimalC', 'fun': gurobi_optimal_const, 'title': "Optimal"},
    #{'short': 'gurobi',  'fun': gurobi_optimal_const, 'title': "Optimal w/Gurobi"}
]

method_funs_const = {cm['short']: cm['fun'] for cm in method_dicts_const}
method_funs_land = {lm['short']: lm['fun'] for lm in method_dicts_land}

all_const_methods = [cm['short'] for cm in method_dicts_const]
all_land_methods = [lm['short'] for lm in method_dicts_land]
#all_const_methods.remove('gurobi')
all_land_methods.remove('gurobi')

land_stats = {
    'land': [
        'land_dispar',
        'land_alloc',
    ],
    'const': [
        'const_opt_diff',
        'const_entropy_diff',
    ],
    'pairs': [
        'min_seat_share',
        'max_neg_marg',
        'neg_marg_count',
        'opt_opt_diff',
    ],
}

party_stats = [
    'party_dispar',
    'party_alloc'
]

scalar_stats = [
    'entropy_diff',
    'failure_rate',
    'total_land_disparity',
]

matrix_stats = [
    'seats_minus_shares',
    'opt_diff',
]

method_measures = [
    *matrix_stats,
    *scalar_stats,
    'land_dispar',
    'party_dispar'
]

by_land = matrix_stats + land_stats['land'] + land_stats['pairs']
by_party = matrix_stats + party_stats

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
