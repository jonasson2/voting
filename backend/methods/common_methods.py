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

def max_absolute_margin(*args, **_):
    reason = "Max next-in and next-but-one-in vote score difference"
    heading = "Margin"
    return common_allocate(*args, absolute_margin, heading, reason)

def max_relative_margin(*args, **_):
    reason = "Max next-in and next-but-one-in vote score ratio"
    heading = "Relative margin"
    return common_allocate(*args, relative_margin, heading, reason)

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

def vote_percentage(votes, alloc, div, **kwargs):
    votesum = kwargs["votesum"]
    pct = votes/votesum/div[alloc]
    party = np.argmax(pct)
    return party, pct[party]

def absolute_margin(votes, alloc, div, **_):
    quot = votes/div[alloc]
    party = np.argmax(quot)
    margin = (quot[party] - np.delete(quot, party)).min()
    return party, margin

def relative_margin(votes, alloc, div, **_):
    quot = votes/div[alloc]
    party = np.argmax(quot)
    others = np.delete(quot, party)
    margin = 10000000 if others.min() == 0 else (quot[party]/others).min()
    return party, margin

def seat_share(votes, alloc, div, **kwargs):
    votesum = kwargs["votesum"]
    totconstseats = kwargs["totconstseats"]
    ss = totconstseats*votes/votesum/div[alloc]
    party = np.argmax(ss)
    return party, ss[party]

def superiority_simple(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='simple')

def superiority_medium(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='medium')

def superiority_full(*args, **kwargs):
    return compute_superiority(*args, **kwargs, kind='full')

def compute_superiority(votes, alloc, div, **kwargs):
    nfree, npartyseats, kind = get("nfree", "npartyseats", "kind")(kwargs)
    score = votes/div[alloc]
    seats = alloc.copy()
    party_next = np.argmax(score)
    score_next = score[party_next]
    if kind=="simple":
        seats[party_next] += 1
        score[party_next] = votes[party_next]/div[seats[party_next]]
    else: # medium or full
        score[party_next] = 0
    nalloc = 1
    print("party_next=", party_next, ", nfree=", nfree)
    while True:
        if all(score == 0):
            return party_next, 10000000
        party = np.argmax(score)
        print("party=", party, ", score=", score)
        if nalloc >= nfree:
            superiority = score_next/score[party]
            print("superiority=", superiority)
            return party_next, superiority
        seats[party] += 1
        score[party] = votes[party]/div[seats[party]]
        nalloc += 1
        if kind == "full" and seats[party] >= npartyseats[party]:
            print("************************")
            score[party] = 0
