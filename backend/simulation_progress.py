"""Periodic replicate counts and a summary of distributed simulation progress."""

import time

from parsim.common import atomic_json


INTERVAL = 5


class ReplicateMonitor:
    """Each CPU updates its own counter, at most once per reporting interval."""

    def __init__(self, counts, totals):
        self.counts = counts
        self.totals = totals
        self.last_update = 0

    def monitor(self, tasknr, iteration):
        now = time.monotonic()
        if iteration == self.totals[tasknr] or now - self.last_update >= INTERVAL:
            self.counts[tasknr] = iteration
            self.last_update = now
        return False


def write_progress(path, counts, total, started):
    atomic_json(path, {"completed": sum(counts[:]), "assigned": total,
                       "elapsed": time.monotonic() - started})


def duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"


class ProgressDisplay:
    def __init__(self):
        self.previous = {}
        self.rates = {}

    def line(self, nodes, snapshots, finished, elapsed):
        completed = 0
        remaining = 0
        estimating = True
        total = sum(node["replicates"] for node in nodes)
        for node in nodes:
            node_id = node["id"]
            assigned = node["replicates"]
            if node_id in finished:
                completed += assigned
                continue
            sample = snapshots.get(node_id, {"completed": 0, "elapsed": 0})
            count = sample["completed"]
            completed += count
            previous_count, previous_elapsed = self.previous.get(node_id, (0, 0))
            delta = count - previous_count
            interval = sample["elapsed"] - previous_elapsed
            if delta > 0 and interval > 0:
                self.rates[node_id] = delta / interval
            self.previous[node_id] = (count, sample["elapsed"])
            if count < assigned:
                rate = self.rates.get(node_id)
                if rate:
                    remaining = max(remaining, (assigned - count) / rate)
                else:
                    estimating = False
        left = duration(remaining) if estimating else "--"
        return (f"Completed {completed:,} / {total:,} ({100 * completed / total:.1f}%)"
                f" | {len(nodes)} nodes, {len(finished)} finished"
                f" | elapsed {duration(elapsed)} | remaining {left}")
