"""Select exact ties and optionally report the allocation decision."""

import numpy as np

from randomness import random_index


def select(scores, on_tie=None, *, minimum=False, rng=None):
    """Return a flat index, preferring table order unless an RNG is supplied."""
    scores = np.asarray(scores)
    if on_tie is None and rng is None:
        return int(scores.argmin() if minimum else scores.argmax())
    best = scores.min() if minimum else scores.max()
    tied = np.flatnonzero(scores == best)
    return select_tied(tied, best, on_tie, rng=rng)


def select_tied(tied, score, on_tie=None, *, rng=None):
    """Choose among already identified best candidates without rescanning scores."""
    winner = int(tied[0])
    if len(tied) == 1:
        return winner
    if rng is not None:
        winner = int(tied[random_index(rng, len(tied))])
    if on_tie is not None and np.isfinite(score):
        on_tie(tied, winner, float(score))
    return winner


def remap(on_tie, indices):
    """Translate local candidate indices to the enclosing allocation's order."""
    if on_tie is None:
        return None
    indices = np.asarray(indices)

    def report(tied, winner, score):
        mapped = list(dict.fromkeys(int(i) for i in indices[tied]))
        if len(mapped) > 1:
            on_tie(mapped, int(indices[winner]), score)

    return report


class TieReport:
    def __init__(self):
        self.events = []

    def reporter(self, stage, labels):
        def report(tied, winner, score):
            event = {
                "stage": stage,
                "candidates": [labels[int(i)] for i in tied],
                "selected": labels[winner],
                "scores": [score],
            }
            # The same candidates may tie at several quotients or recalculations.
            previous = next((previous for previous in self.events
                             if all(previous[key] == event[key]
                                    for key in ("stage", "candidates", "selected"))), None)
            if previous is None:
                self.events.append(event)
            elif score not in previous["scores"]:
                previous["scores"].append(score)
        return report
