from common_flex_allocate import allocate_with_bounds, next_quotient, quotient_scores


def max_const_votes(*args, **kwargs):
    """Meet constituency minima, then allocate the bounded pool by next quotient."""
    allocation, demo = allocate_with_bounds(
        *args, next_quotient, "Vote score", "Maximum over all eligible lists",
        vote_floor=None, flex_scores=quotient_scores, **kwargs)
    return allocation, {"data": demo["data"]["sequence"], "function": print_demo_table}


def print_demo_table(rules, steps):
    headers = [
        "Adjustment seat #", "Constituency", "Party", "Criteria", "Vote score",
    ]
    data = [[
        number,
        rules["constituencies"][step["constituency"]]["name"],
        rules["parties"][step["party"]],
        step["reason"],
        step["quotient"],
    ] for number, step in enumerate(steps, start=1)]
    return headers, data, "Allocation of adjustment seats"
