#!/usr/bin/env python3
"""Check Ricca et al. (2012), Table 3, using the allocations in Table 1.

No full-election allocation method is implemented. In each 2x2 subproblem,
recompute fair shares with the inherited integer margins, then enumerate
every feasible allocation for L1, squared L2 and maximum absolute error.
An independent exact-rational midpoint check verifies every result.

The printed fair shares replace votes: row/column scaling preserves 2x2
cross-product ratios. Their limited precision is covered by conservative
intervals of +/- one and two units of the last printed decimal place.
Requires Python 3 and pdftotext. Writes the experiment summary as JSON.
"""

import argparse
from decimal import Decimal
from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path
import re
import subprocess


ROWS = "P1 P2 L1 L2 L3 TA V1 V2 FV LI ER TO UM MA La1 La2 AB MO C1 C2 PU BA CA S1 S2 SA".split()
METHODS = {"MinMaxLexBest": 2, "MinL1": 3, "MinL2": 4}


def read_table(pdf):
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                          check=True, capture_output=True, text=True).stdout
    quotas, units = [], []
    seats = {method: [] for method in METHODS}
    for i, name in enumerate(ROWS):
        matches = re.findall(r"^" + re.escape(name) + r"\s+(\d[^\n]+)$", text, re.M)
        assert len(matches) == 1, (name, matches)
        entries = matches[0].split()
        assert len(entries) == 26, (name, entries)
        tokens = [entries[5*j] for j in range(5)]

        def expand(values, svp):
            # LN and MPA are compressed into one column in the printed table.
            return [values[0], values[1] if i < 14 else 0,
                    values[1] if i >= 14 else 0, *values[2:], svp]

        svp = 3 if name == "TA" else 0
        quotas.append(expand([F(s) for s in tokens], F(svp)))
        units.append(expand([F(Decimal(1).scaleb(Decimal(s).as_tuple().exponent))
                             for s in tokens], F(0)))
        for method, offset in METHODS.items():
            row = expand([int(entries[5*j+offset]) for j in range(5)], svp)
            assert sum(row) == int(entries[-1]) + svp
            seats[method].append(row)
    for matrix in seats.values():
        assert [sum(row[j] for row in matrix) for j in range(7)] == [255, 57, 8, 226, 30, 38, 3]
    assert seats["MinL1"] == seats["MinL2"]
    return quotas, units, seats


def margins(x):
    a, b, c, d = x
    r1, r2, c1 = a+b, c+d, a+c
    return r1, r2, c1, max(0, c1-r2), min(r1, c1)


def reference(q, x):
    r1, r2, c1, lo, hi = margins(x)
    if lo == hi or 0 in q:
        return list(map(float, x))
    a, b, c, d = map(float, q)
    for _ in range(70):
        z = (lo+hi)/2
        p = b*c*z*(r2-c1+z) - a*d*(r1-z)*(c1-z)
        if p < 0:
            lo = z
        else:
            hi = z
    z = (lo+hi)/2
    return [z, r1-z, c1-z, r2-c1+z]


def exhaustive(q, x):
    target = reference(q, x)
    r1, r2, c1, lo, hi = margins(x)
    if 0 in q:
        return True, False  # A structural zero fixes the sole degree of freedom.
    outcomes = []
    for objective in (lambda es: sum(abs(e) for e in es),
                      lambda es: sum(e*e for e in es),
                      lambda es: max(abs(e) for e in es)):
        costs = []
        for z in range(lo, hi+1):
            y = [z, r1-z, c1-z, r2-c1+z]
            costs.append(objective([y[j]-target[j] for j in range(4)]))
        best = min(costs)
        outcomes.append([lo+k for k, v in enumerate(costs) if abs(v-best) < 1e-10])
    assert outcomes[0] == outcomes[1] == outcomes[2], (q, x, outcomes)
    return x[0] in outcomes[0], len(outcomes[0]) > 1


def boundary(A, B, x, k):
    """Four times the cross-product polynomial at the half-integer k/2."""
    r1, r2, c1, _, _ = margins(x)
    return B*k*(2*(r2-c1)+k) - A*(2*r1-k)*(2*c1-k)


def exact(q, x):
    _, _, _, lo, hi = margins(x)
    if lo == hi or 0 in q:
        return True, False
    a, b, c, d = q
    lower = boundary(a*d, b*c, x, 2*x[0]-1) if x[0] > lo else -1
    upper = boundary(a*d, b*c, x, 2*x[0]+1) if x[0] < hi else 1
    return lower <= 0 and upper >= 0, lower == 0 or upper == 0


def rounding_class(q, units, x, multiplier):
    _, _, _, lo, hi = margins(x)
    if lo == hi or 0 in q:
        return "certain_pass"
    lows = [a-multiplier*b for a, b in zip(q, units)]
    highs = [a+multiplier*b for a, b in zip(q, units)]
    assert min(lows) > 0
    amin, amax = lows[0]*lows[3], highs[0]*highs[3]
    bmin, bmax = lows[1]*lows[2], highs[1]*highs[2]
    lower = boundary(amin, bmax, x, 2*x[0]-1) if x[0] > lo else -1
    upper = boundary(amax, bmin, x, 2*x[0]+1) if x[0] < hi else 1
    if lower < 0 and upper > 0:
        return "certain_pass"
    lower = boundary(amax, bmin, x, 2*x[0]-1) if x[0] > lo else -1
    upper = boundary(amin, bmax, x, 2*x[0]+1) if x[0] < hi else 1
    if lower > 0 or upper < 0:
        return "certain_fail"
    return "uncertain"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=Path(__file__).resolve().parents[3]
                        / "kosningagrein/references/ricca-et-al.pdf")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.json"))
    args = parser.parse_args()
    quotas, units, seats = read_table(args.pdf)

    # Example 3, p.568: inherited allocation fails; the new allocation passes.
    example_votes = list(map(F, [30, 82, 32, 98]))
    old, new = [3, 7, 2, 9], [2, 8, 3, 8]
    assert exhaustive(example_votes, old) == exact(example_votes, old) == (False, False)
    assert exhaustive(example_votes, new) == exact(example_votes, new) == (True, False)
    assert abs(reference(example_votes, old)[0]-2.4891) < 0.00005
    summary = {"source": str(args.pdf), "example3_reference": reference(example_votes, old),
               "example3_verified": True, "methods": {}}
    for method in METHODS:
        stats = {scope: {"total": 0, "pass": 0, "ties": 0,
                         "rounding": {str(m): {"certain_pass": 0, "certain_fail": 0, "uncertain": 0}
                                      for m in (1, 2)}} for scope in ("all", "four_positive")}
        for rows in combinations(range(26), 2):
            for cols in combinations(range(7), 2):
                cells = [(i, j) for i in rows for j in cols]
                q = [quotas[i][j] for i, j in cells]
                u = [units[i][j] for i, j in cells]
                x = [seats[method][i][j] for i, j in cells]
                passed, tie = exhaustive(q, x)
                assert (passed, tie) == exact(q, x), (method, rows, cols, q, x)
                classes = {str(m): rounding_class(q, u, x, m) for m in (1, 2)}
                for scope in ("all", "four_positive") if min(q) > 0 else ("all",):
                    s = stats[scope]
                    s["total"] += 1
                    s["pass"] += passed
                    s["ties"] += tie
                    for m, classification in classes.items():
                        s["rounding"][m][classification] += 1
        for s in stats.values():
            s["percent"] = 100*s["pass"]/s["total"]
            for bound in s["rounding"].values():
                bound["percent_bounds"] = [100*bound["certain_pass"]/s["total"],
                                           100*(s["total"]-bound["certain_fail"])/s["total"]]
        summary["methods"][method] = stats
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
