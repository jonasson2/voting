from copy import deepcopy
from pathlib import Path


class VoteTableFormatError(ValueError):
    pass


def _is_blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _text(value):
    return "" if value is None else str(value).strip()


def _nonnegative_int(value, description, *, blank=0):
    if _is_blank(value):
        return blank
    if isinstance(value, bool):
        raise VoteTableFormatError(f"{description} must be a non-negative integer")
    if isinstance(value, int):
        result = value
    elif isinstance(value, float) and value.is_integer():
        result = int(value)
    elif isinstance(value, str) and value.isascii() and value.isdigit():
        result = int(value)
    else:
        raise VoteTableFormatError(f"{description} must be a non-negative integer")
    if result < 0:
        raise VoteTableFormatError(f"{description} must be a non-negative integer")
    return result


def empty_party_vote_info():
    return {
        "name": "–",
        "num_fixed_seats": 0,
        "num_adj_seats": 0,
        "votes": [],
        "specified": False,
        "total": 0,
        "pruned": 0,
    }


def add_empty_party_votes(vote_table):
    vote_table["party_vote_info"] = empty_party_vote_info()
    return vote_table


def _normalise_rows(rows):
    rows = [list(row) for row in rows]
    while rows and all(_is_blank(value) for value in rows[-1]):
        rows.pop()
    if not rows:
        raise VoteTableFormatError("The vote file is empty")

    width = len(rows[0])
    if width < 4:
        raise VoteTableFormatError(
            "The vote file must contain seat columns and at least one party"
        )

    normalised = []
    for row_number, row in enumerate(rows, start=1):
        if all(_is_blank(value) for value in row):
            normalised.append([None] * width)
        elif len(row) != width:
            raise VoteTableFormatError(
                f"Row {row_number} has {len(row)} columns; expected {width}"
            )
        else:
            normalised.append(row)
    return normalised


def _parse_vote_table(rows, filename):
    rows = _normalise_rows(rows)
    header = rows.pop(0)

    if _text(header[1]).lower() not in {"fixed", "cons"}:
        raise VoteTableFormatError(
            'Heading of second column must be "fixed" (for fixed seats)'
        )

    third_heading = _text(header[2]).lower()
    if third_heading == "adj":
        has_maximum = False
        party_start = 3
    elif (third_heading == "min_adj" and len(header) > 3
          and _text(header[3]).lower() == "max_adj"):
        has_maximum = True
        party_start = 4
    else:
        raise VoteTableFormatError(
            'Adjustment-seat headings must be "adj", or "min_adj" and "max_adj"'
        )

    has_pruned = _text(header[-1]).lower() == "pruned"
    party_end = len(header) - 1 if has_pruned else len(header)
    parties = header[party_start:party_end]
    if not parties:
        raise VoteTableFormatError("The vote file contains no parties")
    if not all(isinstance(party, str) and party.strip() for party in parties):
        raise VoteTableFormatError("Party abbreviations must be non-blank text")
    parties = [party.strip() for party in parties]

    party_names = None
    maximum_total = None
    seen_metadata = set()
    while rows:
        row_name = _text(rows[0][0]).lower()
        if row_name not in {"party names", "max adj seats"}:
            break
        if row_name in seen_metadata:
            raise VoteTableFormatError(f'Duplicate metadata row "{rows[0][0]}"')
        seen_metadata.add(row_name)
        row = rows.pop(0)

        if row_name == "party names":
            if any(not _is_blank(value) for value in row[1:party_start]):
                raise VoteTableFormatError("Party names row must have blank seat cells")
            if has_pruned and not _is_blank(row[-1]):
                raise VoteTableFormatError(
                    "Party names row must have a blank pruned-votes cell"
                )
            names = [_text(value) for value in row[party_start:party_end]]
            party_names = names if any(names) else None
        else:
            if not has_maximum:
                raise VoteTableFormatError(
                    "Max adj seats row requires min_adj and max_adj columns"
                )
            if any(not _is_blank(value) for value in row[1:3]):
                raise VoteTableFormatError(
                    "Max adj seats row must have blank fixed and minimum-seat cells"
                )
            maximum_total = _nonnegative_int(row[3], "Max adj seats")
            if any(not _is_blank(value) for value in row[party_start:party_end]):
                raise VoteTableFormatError(
                    "Max adj seats row must have blank party-vote cells"
                )
            if has_pruned and not _is_blank(row[-1]):
                raise VoteTableFormatError(
                    "Max adj seats row must have a blank pruned-votes cell"
                )

    if has_maximum and maximum_total is None:
        raise VoteTableFormatError(
            "Min_adj and max_adj columns require a Max adj seats row"
        )

    separators = [
        index for index, row in enumerate(rows)
        if all(_is_blank(value) for value in row)
    ]
    if separators:
        if len(separators) != 1 or separators[0] != len(rows) - 2:
            raise VoteTableFormatError(
                "A blank row may appear only immediately before national party votes"
            )
        constituency_rows = rows[:separators[0]]
        national_row = rows[-1]
    else:
        constituency_rows = rows
        national_row = None

    if not constituency_rows:
        raise VoteTableFormatError("The vote file contains no constituencies")

    constituencies = []
    votes = []
    pruned = []
    for row_number, row in enumerate(constituency_rows, start=2):
        name = _text(row[0])
        if not name:
            raise VoteTableFormatError(
                f"Constituency name is blank in row {row_number}"
            )
        fixed = _nonnegative_int(row[1], f"Fixed seats in {name}")
        minimum = _nonnegative_int(row[2], f"Adjustment seats in {name}")
        constituency = {
            "name": name,
            "num_fixed_seats": fixed,
            "num_adj_seats": minimum,
        }
        if has_maximum:
            maximum = _nonnegative_int(
                row[3], f"Maximum adjustment seats in {name}", blank=None
            )
            if maximum is not None and maximum < minimum:
                raise VoteTableFormatError(
                    f"Maximum adjustment seats in {name} may not be below the minimum"
                )
            constituency["max_adj_seats"] = maximum
        constituencies.append(constituency)
        votes.append([
            _nonnegative_int(value, f"Votes in row {row_number}")
            for value in row[party_start:party_end]
        ])
        pruned.append(
            _nonnegative_int(row[-1], f"Pruned votes in {name}")
            if has_pruned else 0
        )

    result = {
        "name": (_text(header[0])
                 or Path(str(filename)).stem),
        "parties": parties,
        "votes": votes,
        "pruned": pruned,
        "constituencies": constituencies,
        "party_vote_info": empty_party_vote_info(),
    }
    if party_names:
        result["party_names"] = party_names
    if has_maximum:
        result["max_total_adj_seats"] = maximum_total

    if national_row is not None:
        name = _text(national_row[0])
        if not name:
            raise VoteTableFormatError("The national party vote name is blank")
        if has_maximum and not _is_blank(national_row[3]):
            raise VoteTableFormatError(
                "The national party vote row must have a blank max_adj cell"
            )
        national_votes = [
            _nonnegative_int(value, "National party votes")
            for value in national_row[party_start:party_end]
        ]
        national_pruned = (
            _nonnegative_int(national_row[-1], "National pruned votes")
            if has_pruned else 0
        )
        result["party_vote_info"] = {
            "name": name,
            "num_fixed_seats": _nonnegative_int(
                national_row[1], "National fixed seats"
            ),
            "num_adj_seats": _nonnegative_int(
                national_row[2], "National adjustment seats"
            ),
            "votes": national_votes,
            "specified": True,
            "total": sum(national_votes) + national_pruned,
            "pruned": national_pruned,
        }
    return result


def process_vote_table(rows, filename):
    try:
        return _parse_vote_table(rows, filename)
    except VoteTableFormatError as error:
        return str(error)


def _require_nonnegative_int(value, description):
    if type(value) is not int:
        raise TypeError(f"{description} must be an integer.")
    if value < 0:
        raise ValueError(f"{description} may not be negative.")


def check_vote_table(vote_table):
    if not isinstance(vote_table, dict):
        raise TypeError("The vote table must be an object.")
    table = deepcopy(vote_table)

    name = table.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("The vote table name must be non-blank text.")
    table["name"] = name.strip()

    parties = table.get("parties")
    if (not isinstance(parties, list) or not parties
            or not all(isinstance(party, str) and party.strip()
                       for party in parties)):
        raise ValueError("The party list must contain non-blank text.")
    table["parties"] = [party.strip() for party in parties]
    num_parties = len(parties)

    constituencies = table.get("constituencies")
    if not isinstance(constituencies, list) or not constituencies:
        raise ValueError("The vote table must contain constituencies.")
    num_constituencies = len(constituencies)

    votes = table.get("votes")
    if not isinstance(votes, list) or len(votes) != num_constituencies:
        raise ValueError("The vote table does not match the constituency list.")
    for row in votes:
        if not isinstance(row, list) or len(row) != num_parties:
            raise ValueError("The vote table does not match the party list.")
        for value in row:
            _require_nonnegative_int(value, "Votes")

    party_names = table.get("party_names")
    if party_names is not None:
        if not isinstance(party_names, list) or len(party_names) != num_parties:
            raise ValueError("Party names do not match the party list.")
        if not all(isinstance(party_name, str) for party_name in party_names):
            raise TypeError("Party names must be text.")
        party_names = [party_name.strip() for party_name in party_names]
        if any(party_names):
            table["party_names"] = party_names
        else:
            table.pop("party_names", None)

    pruned = table.setdefault("pruned", [0] * num_constituencies)
    if not isinstance(pruned, list) or len(pruned) != num_constituencies:
        raise ValueError("The pruned vote totals do not match the constituencies.")
    for value in pruned:
        _require_nonnegative_int(value, "Pruned votes")

    has_maximum = "max_total_adj_seats" in table
    for constituency in constituencies:
        if not isinstance(constituency, dict):
            raise TypeError("Each constituency must be an object.")
        constituency_name = constituency.get("name")
        if not isinstance(constituency_name, str) or not constituency_name.strip():
            raise ValueError("Constituency names must be non-blank text.")
        constituency["name"] = constituency_name.strip()
        if "num_fixed_seats" not in constituency and "num_const_seats" in constituency:
            constituency["num_fixed_seats"] = constituency.pop("num_const_seats")
        for key, description in (
            ("num_fixed_seats", "Fixed seats"),
            ("num_adj_seats", "Adjustment seats"),
        ):
            if key not in constituency:
                raise KeyError(f"Missing {description.lower()} for {constituency_name}.")
            _require_nonnegative_int(constituency[key], description)
        if has_maximum:
            if "max_adj_seats" not in constituency:
                raise KeyError(
                    f"Missing maximum adjustment seats for {constituency_name}."
                )
            maximum = constituency["max_adj_seats"]
            if maximum == "":
                maximum = None
                constituency["max_adj_seats"] = None
            if maximum is not None:
                _require_nonnegative_int(maximum, "Maximum adjustment seats")
                if maximum < constituency["num_adj_seats"]:
                    raise ValueError(
                        "Maximum adjustment seats may not be below the minimum."
                    )

    if has_maximum:
        maximum_total = table["max_total_adj_seats"]
        _require_nonnegative_int(maximum_total, "Maximum total adjustment seats")
        minimum_total = sum(
            constituency["num_adj_seats"] for constituency in constituencies
        )
        if maximum_total < minimum_total:
            raise ValueError(
                "Maximum total adjustment seats may not be below the minimum total."
            )
        finite_maxima = [
            constituency["max_adj_seats"] for constituency in constituencies
        ]
        if (all(maximum is not None for maximum in finite_maxima)
                and maximum_total > sum(finite_maxima)):
            raise ValueError(
                "Maximum total adjustment seats exceeds constituency maxima."
            )

    if "party_votes" in table:
        table["party_vote_info"] = table.pop("party_votes")
    party_vote_info = table.get("party_vote_info")
    if party_vote_info is None:
        party_vote_info = empty_party_vote_info()
        table["party_vote_info"] = party_vote_info
    if not isinstance(party_vote_info, dict):
        raise TypeError("National party vote information must be an object.")
    party_vote_info.setdefault("pruned", 0)
    party_vote_info.setdefault("specified", False)
    party_vote_info.setdefault("name", "–")
    party_vote_info.setdefault("num_fixed_seats", 0)
    party_vote_info.setdefault("num_adj_seats", 0)
    party_vote_info.setdefault("votes", [])
    if type(party_vote_info["specified"]) is not bool:
        raise TypeError("The national party vote specified flag must be boolean.")
    national_name = party_vote_info["name"]
    if not isinstance(national_name, str):
        raise TypeError("The national party vote name must be text.")
    if party_vote_info["specified"] and not national_name.strip():
        raise ValueError("The national party vote name must be non-blank text.")
    party_vote_info["name"] = national_name.strip()
    _require_nonnegative_int(party_vote_info["num_fixed_seats"],
                             "National fixed seats")
    _require_nonnegative_int(party_vote_info["num_adj_seats"],
                             "National adjustment seats")
    _require_nonnegative_int(party_vote_info["pruned"], "National pruned votes")
    national_votes = party_vote_info["votes"]
    if party_vote_info["specified"]:
        if not isinstance(national_votes, list) or len(national_votes) != num_parties:
            raise ValueError("National party votes do not match the party list.")
        for value in national_votes:
            _require_nonnegative_int(value, "National party votes")
        party_vote_info["total"] = (
            sum(national_votes) + party_vote_info["pruned"]
        )
    else:
        party_vote_info["votes"] = []
        party_vote_info["total"] = 0

    valid_bases = {"totals", "party_vote_info", "average"}
    basis = table.get("party_vote_basis", "totals")
    if basis not in valid_bases:
        raise ValueError(f"Unknown party vote basis: {basis}")
    table["party_vote_basis"] = (
        basis if party_vote_info["specified"] else "totals"
    )
    return table
