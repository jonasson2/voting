import sys
sys.path.append('../backend')
sys.path.append('../backend/methods')
from nearest_to_previous import nearest_to_previous
from switching import switching
from relative_superiority import relative_superiority
from max_const_seat_share import max_const_seat_share
from max_vote_percentage import max_vote_percentage
from switching import switching
from alternating_scaling import alt_scaling
from farthest_from_next import farthest_from_next
from gurobi_optimal import gurobi_optimal
from germany_methods import parties_first, länder_first, max_share, max_relative_margin, \
    max_absolute_margin, scandinavian, optimal_const, gurobi_const

land_method_dicts = [
    #'swi':  (switching,                 "Switching"),
    #'rsup': (relative_superiority,      "Relative superiority"),
    #'seatsh':   (max_const_seat_share,      "Max seat share"),
    {'short': 'votepct', 'fun': max_vote_percentage, 'title': "Max vote share"},
    {'short': 'relmarg', 'fun': farthest_from_next, 'title': "Relative margin"},
    {'short': 'nearprev', 'fun': nearest_to_previous, 'title': "Nearest to previous"},
    {'short': 'optimal', 'fun': alt_scaling, 'title': 'Optimal'},
    {'short': 'switch', 'fun': switching, 'title': 'Seat switching'},
    {'short': 'party1st', 'fun': parties_first, 'title': "Parties first"},
    {'short': 'land1st', 'fun': länder_first, 'title': "Länder first"},
    {'short': 'gurobi', 'fun': gurobi_optimal, 'title': "Optimal w/Gurobi"},
]

const_method_dicts = [
    {'short': 'scand', 'fun': scandinavian, 'title': "Scandinavian"},
    {'short': 'votepct', 'fun': max_share, 'title': "Max vote percentage"},
    {'short': 'relmarg', 'fun': max_relative_margin, 'title': "Max relative margin"},
    {'short': 'absmarg', 'fun': max_absolute_margin, 'title': "Max absolute margin"},
    {'short': 'optconst', 'fun': optimal_const, 'title': "Optimal"},
    {'short': 'gurobi', 'fun': gurobi_const, 'title': "Optimal w/Gurobi"}
]

party_measure_dicts = {
    'min_party_dispar': ('Maximum party disparity', 'min', '.3f'),
    'max_party_dispar': ('Maximum party disparity', 'max', '.3f'),
    'party_alloc':      ('Bundeswide party allocations', 'sum', '.2f')
}

land_measure_dicts = {
    'max_neg_marg':    ('Maximum negative margin',  'max', '.2%'),
    'min_seat_share':  ('Minimum seat share',       'min', '.2%'),
    'min_land_dispar': ('Maximum land disparity',   'min', '.3f'),
    'max_land_dispar': ('Maximum land disparity',   'max', '.3f'),
    'neg_marg_count':  ('Negative margin count',    'sum', '.3f'),
    'land_alloc':      ('Land allocations',         'sum', '.2f'),
}
alloc_measures = ['party_alloc', 'land_alloc']

const_method_funs = {cm['short']: cm['fun'] for cm in const_method_dicts}
land_method_funs = {lm['short']: lm['fun'] for lm in land_method_dicts}

all_const_methods = [cm['short'] for cm in const_method_dicts]
all_land_methods = [lm['short'] for lm in land_method_dicts]
party_measures = list(party_measure_dicts.keys())
land_measures = list(land_measure_dicts.keys())
measure_dicts = {**party_measure_dicts, **land_measure_dicts}
measure_formats = {m: v[2] for (m,v) in measure_dicts.items()}
measure_formats[''] = '.2f'

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

party_land_measures = {
}
