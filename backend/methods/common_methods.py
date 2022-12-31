# coding:utf-8
import numpy as np
from common_allocate import common_allocate
from operator import itemgetter as get

def max_const_vote_percentage(*args, **_):
    heading = "Const. vote score percentage"
    reason = "Max over all lists"
    return common_allocate(*args, vote_percentage, heading, reason)

def max_const_seat_share(*args, **_):
    heading = "Const. seat share score"
    reason = "Max over all lists"
    return common_allocate(*args, seat_share, heading, reason)

def nearest_to_previous(*args, last=None, **_):
    heading = "Score/ratio of scores"
    reason = "Maximum ratio of previous in to next in score"
    nolast_reason = "No fixed seat, thus using maximum score"
    return common_allocate(*args, nearest_to_prev_ratio, heading, reason,
                           last=last, nolast_reason=nolast_reason)
    
def relative_superiority(*args, **_):
    reason = "Max ratio of next-in vote score to first substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_full, heading, reason)

def rel_sup_medium(*args, **_):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_medium, heading, reason)

def rel_sup_simple(*args, **_):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_simple, heading, reason)

def rel_sup_next(*args, **_):
    pass

def nearest_to_prev_ratio(votes, alloc, div, **kwargs):
    last_party = kwargs["last_party"]
    if last_party and last_party >= 0:
        last_score = votes[last_party]/div[alloc[last_party] - 1]
    else:
        last_score = 1
    score = votes/div[alloc]
    ratio = score/last_score
    party = np.argmax(ratio)
    return party, ratio[party]

def vote_percentage(votes, alloc, div, **_):
    pct = votes/div[alloc]/votes.sum()
    party = np.argmax(pct)
    return party, pct[party]

def seat_share(votes, alloc, div, **kwargs):
    nseats = kwargs["nseats"]
    ss = nseats.sum()*votes/div[alloc]/votes.sum()
    party = np.argmax[ss]
    return party, ss[party]

def superiority_simple(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='simple')

def superiority_medium(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='medium')

def superiority_full(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='full')

def compute_superiority(votes, alloc, div, **kwargs):
    nseats, npartyseats, kind = get("nseats", "npartyseats", "kind")(kwargs)
    score = votes/div[alloc]
    seats = alloc.copy()
    party_next = np.argmax(score)
    score_next = score[party_next]
    if kind=="simple":
        score[party_next] = 0
    else:
        seats[party_next] += 1
    nalloc = 1
    nfree = nseats - seats.sum()
    while True:
        if all(score == 0):
            return party_next, 10000000
        party = np.argmax(score)
        seats[party] += 1
        score[party] = votes[party]/div[seats[party]]
        nalloc += 1
        if nalloc > nfree:
            superiority = score_next/score[party]
            return party_next, superiority
        if kind == "full" and seats[party] >= npartyseats[party]:
            score[party] = 0
