"""Select exact ties and optionally report the allocation decision."""

import numpy as np

from randomness import random_index


def select(scores, on_tie=None, *, minimum=False, rng=None):
    """Return a flat index, preferring table order unless an RNG is supplied."""
    scores = np.asarray(scores)
    best = scores.min() if minimum else scores.max()
    tied = np.flatnonzero(scores == best)
    winner = int(tied[random_index(rng, len(tied))]
                 if rng is not None else tied[0])
    if on_tie is not None and len(tied) > 1 and np.isfinite(best):
        on_tie(tied, winner, float(best))
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
        def report(tied, winner, _score):
            event = {
                "stage": stage,
                "candidates": [labels[int(i)] for i in tied],
                "selected": labels[winner],
            }
            # The same candidates may tie at several quotients or recalculations.
            if event not in self.events:
                self.events.append(event)
        return report
