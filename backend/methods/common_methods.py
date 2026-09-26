# coding:utf-8
import numpy as np
from common_allocate import common_allocate
from allocate_pool import next_quotient
from operator import itemgetter as get

def max_const_vote_percentage(*args, **kwargs):
    heading = "Const. vote score percentage"
    reason = "Max over all lists"
    return common_allocate(*args, vote_percentage, heading, reason,
                           flex_scores=vote_percentage_scores, **kwargs)

def max_const_seat_share(*args, **kwargs):
    # print('in max_const_seat_share')
    heading = "Const. seat share score"
    reason = "Max over all lists"
    return common_allocate(*args, seat_share, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def seats_p_unbounded(*args, **kwargs):
    # print('in seats_p_unbounded')
    heading = "Seat share score"
    reason = "Max over all lists"
    return common_allocate(*args, seat_share, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def nearest_to_previous(*args, last=None, **kwargs):
    heading = "Score/ratio of scores"
    reason = "Maximum ratio of previous in to next in score"
    nolast_reason = "No fixed seat, thus using maximum score"
    return common_allocate(*args, nearest_to_prev_ratio, heading, reason,
                           last=last, nolast_reason=nolast_reason, **kwargs)
    
def relative_superiority(*args, **kwargs):
    reason = "Max ratio of next-in vote score to first substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_full, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def max_absolute_margin(*args, **kwargs):
    reason = "Max next-in and next-but-one-in vote score difference"
    heading = "Margin"
    return common_allocate(*args, absolute_margin, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def max_relative_margin(*args, **kwargs):
    reason = "Max next-in and next-but-one-in vote score ratio"
    heading = "Relative margin"
    return common_allocate(*args, relative_margin, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def rel_sup_medium(*args, **kwargs):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_medium, heading, reason,
                           nat_prior_allocations=kwargs.get("nat_prior_allocations"))

def rel_sup_simple(*args, **kwargs):
    reason = "Max ratio of next-in vote score to computed substitute vote score"
    heading = "Superiority ratio"
    return common_allocate(*args, superiority_simple, heading, reason,
                           flex_scores=superiority_pool_scores, **kwargs)

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
    return next_quotient(votes / kwargs["votesum"], alloc, div)


def vote_percentage_scores(votes, alloc, div, *, votesums, **_):
    return votes / votesums[:, None] / div[alloc]


def superiority_pool_scores(votes, alloc, div, *, free_const, free_party,
                            remaining, exclude_zero_votes=False, **_):
    """Score one actual seat using a provisional allocation of the whole pool."""
    active = np.flatnonzero(free_party > 0)
    provisional = alloc.copy()
    room = free_const.copy()
    counts = np.zeros(len(room), dtype=int)
    # The simplified method's lookahead can exceed party deficits.
    for _ in range(remaining):
        quotients = np.full(votes.shape, -np.inf)
        quotients[:, active] = votes[:, active] / div[provisional[:, active]]
        quotients[room <= 0, :] = -np.inf
        if exclude_zero_votes:
            quotients[votes <= 0] = -np.inf
        winner = int(np.argmax(quotients))
        c, p = np.unravel_index(winner, votes.shape)
        if not np.isfinite(quotients[c, p]):
            raise ValueError("No eligible list can receive the remaining seats.")
        provisional[c, p] += 1
        room[c] -= 1
        counts[c] += 1

    scores = np.full(votes.shape, -np.inf)
    for c in np.flatnonzero(counts):
        parties = active
        if exclude_zero_votes:
            parties = parties[votes[c, parties] > 0]
        if len(parties):
            p, score = superiority_simple(
                votes[c, parties], alloc[c, parties], div,
                nfree=counts[c], npartyseats=free_party[parties])
            scores[c, parties[p]] = score
    return scores


def absolute_margin(votes, alloc, div, **_):
    quot = votes/div[alloc]
    party = np.argmax(quot)
    if len(quot) == 1:
        return party, None
    margin = (quot[party] - np.delete(quot, party)).min()
    return party, margin

def relative_margin(votes, alloc, div, **_):
    quot = votes/div[alloc]
    party = np.argmax(quot)
    if len(quot) == 1:
        return party, None
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
    while True:
        if all(score == 0):
            return party_next, 10000000
        party = np.argmax(score)
        if nalloc >= nfree:
            superiority = score_next/score[party]
            return party_next, superiority
        seats[party] += 1
        score[party] = votes[party]/div[seats[party]]
        nalloc += 1
        if kind == "full" and seats[party] >= npartyseats[party]:
            score[party] = 0
