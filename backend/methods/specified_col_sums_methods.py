# coding:utf-8
import numpy as np
from specified_col_sums_allocate import specified_col_sums_allocate
from operator import itemgetter as get

def superiority_simple(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='simple')

def superiority_medium(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='medium')
    
def superiority_full(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='full')

def vote_percentage(votes, alloc, div, **_):
    pct = votes/div[alloc]/votes.sum()
    party = np.argmax(pct)
    return party, pct[party]

def seat_share(votes, alloc, div, **kwargs):
    nseats = kwargs["nseats"]
    ss = votes/div[alloc]/nseats.sum()
    party = np.argmax[ss]
    return party, ss[party]

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

def relative_superiority(*args, **kwargs):
    reason = "Max ratio of next-in vote score to first substitute vote score"
    heading = "Superiority ratio"
    return specified_col_sums_allocate(*args, superiority_full, heading, reason)

def relative_superiority_medium(*args, **kwargs):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return specified_col_sums_allocate(*args, superiority_medium, heading, reason)

def relative_superiority_simple(*args, **kwargs):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return specified_col_sums_allocate(*args, superiority_simple, heading, reason)

def max_const_vote_percentage(*args, **kwargs):
    heading = "Const. vote score percentage"
    reason = "Max over all lists"
    return specified_col_sums_allocate(*args, vote_percentage, heading, reason)

def max_const_seat_share(*args, **kwargs):
    heading = "Const. seat share score"
    reason = "Max over all lists"
    return specified_col_sums_allocate(*args, seat_share, heading, reason)
