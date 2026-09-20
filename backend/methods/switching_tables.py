"""Step-by-step tables shared by adjustment-seat switching methods."""


def print_initial_allocation(rules, steps):
    headers = ["Party", "Nationally apportioned", "All as const. seats", "Off by"]
    data = [[
        rules["parties"][party["party"]],
        party["goal"],
        party["actual"],
        party["actual"] - party["goal"],
    ] for party in steps["initial_allocation"]]
    return headers, data, "Nationally apportioned vs. full constituency allocation"


def print_reassignment_table(rules, steps):
    headers = [
        "Step", "Constituency", "From", "To",
        "Returned quotient", "Recipient quotient",
    ]
    data = [[
        number,
        rules["constituencies"][switch["constituency"]]["name"],
        rules["parties"][switch["from"]],
        rules["parties"][switch["to"]],
        switch["removal_quotient"],
        switch["recipient_quotient"],
    ] for number, switch in enumerate(steps["switches"], start=1)]
    if not data:
        data = [["–", "–", "No switching required", "–", "–", "–"]]
    return headers, data, steps.get("title", "Swedish switching of excess seats")
