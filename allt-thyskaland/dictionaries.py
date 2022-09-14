import sys
sys.path.append('../backend')
sys.path.append('../backend/methods')
from nearest_to_previous import nearest_to_previous
from relative_superiority import relative_superiority
from max_const_seat_share import max_const_seat_share
from max_const_vote_percentage import max_const_vote_percentage
from switching import switching
from farthest_from_next import farthest_from_next
from methods import parties_first, länder_first, max_share, max_advantage, scandinavian

land_methods = [
    #'swi':  (switching,                 "Switching"),
    #'rsup': (relative_superiority,      "Relative superiority"),
    #'seatsh':   (max_const_seat_share,      "Max seat share"),
    {'short': 'votepct', 'fun': max_const_vote_percentage, 'title': "Max vote share"},
    {'short': 'reladv', 'fun': farthest_from_next, 'title': "Relative advantage"},
    {'short': 'nearprev', 'fun': nearest_to_previous, 'title': "Nearest to previous"},
    {'short': 'party1st', 'fun': parties_first, 'title': "Parties first"},
    {'short': 'land1st', 'fun': länder_first, 'title': "Länder first"},
]

const_methods = [
    {'short': 'scand', 'fun': scandinavian, 'title': "Scandinavian"},
    {'short': 'votepct', 'fun': max_share, 'title': "Max vote percentage"},
    {'short': 'reladv', 'fun': max_advantage, 'title': "Relative advantage"},
]

party_measures = [
    {'short': 'party_disparity', 'title':'Party disparity', 'fmt':'.2f'}
]

land_measures = [
    {'short': 'max_neg_margin', 'title': 'Maximum negative margin', 'fmt':'.1%'},
    {'short': 'min_seat_share', 'title': 'Minimum seat share', 'fmt':'.1%'},
    {'short': 'land_disparity', 'title': 'Land disparity', 'fmt':'.2f'},
    {'short': 'neg_marg_freq', 'title': 'Negative margin frequency', 'fmt':'.2f'}
]

measures = land_measures + party_measures

measure_formats = {m['short']: m['fmt'] for m in measures}
measure_formats[''] = '.2f'
short_const_methods = [cm['short'] for cm in const_methods]
short_land_methods = [lm['short'] for lm in land_methods]
short_party_measures = [pm['short'] for pm in party_measures]
short_land_measures = [lm['short'] for lm in land_measures]

land_abbrev = {
 0: 'Sch-Hol',
 1: 'Hamb',
 2: 'N-sachs',
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
