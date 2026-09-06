#!/usr/bin/env python3
import argparse
import csv
import io
import json
from pathlib import Path
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

TABLE = "08092"
BASE = f"https://data.ssb.no/api/pxwebapi/v2/tables/{TABLE}"
LANG = "no"

DISTRICT_ORDER = [
    "v01",
    "v02",
    "v03",
    "v04",
    "v05",
    "v06",
    "v07",
    "v08",
    "v09",
    "v10",
    "v11",
    "v12",
    "v14",
    "v15",
    "v16",
    "v17",
    "v18",
    "v19",
    "v20",
]

TOTAL_SEATS = {
    "2013": {
        "v01": 9,
        "v02": 17,
        "v03": 19,
        "v04": 7,
        "v05": 7,
        "v06": 9,
        "v07": 7,
        "v08": 6,
        "v09": 4,
        "v10": 6,
        "v11": 14,
        "v12": 16,
        "v14": 4,
        "v15": 9,
        "v16": 10,
        "v17": 5,
        "v18": 9,
        "v19": 6,
        "v20": 5,
    },
    "2017": {
        "v01": 9,
        "v02": 17,
        "v03": 19,
        "v04": 7,
        "v05": 7,
        "v06": 9,
        "v07": 7,
        "v08": 6,
        "v09": 4,
        "v10": 6,
        "v11": 14,
        "v12": 16,
        "v14": 4,
        "v15": 9,
        "v16": 10,
        "v17": 5,
        "v18": 9,
        "v19": 6,
        "v20": 5,
    },
    "2021": {
        "v01": 9,
        "v02": 19,
        "v03": 20,
        "v04": 7,
        "v05": 6,
        "v06": 8,
        "v07": 7,
        "v08": 6,
        "v09": 4,
        "v10": 6,
        "v11": 14,
        "v12": 16,
        "v14": 4,
        "v15": 8,
        "v16": 10,
        "v17": 5,
        "v18": 9,
        "v19": 6,
        "v20": 5,
    },
    "2025": {
        "v01": 9,
        "v02": 20,
        "v03": 20,
        "v04": 7,
        "v05": 6,
        "v06": 8,
        "v07": 7,
        "v08": 6,
        "v09": 4,
        "v10": 6,
        "v11": 14,
        "v12": 16,
        "v14": 4,
        "v15": 8,
        "v16": 10,
        "v17": 5,
        "v18": 9,
        "v19": 6,
        "v20": 4,
    },
}

PARTY_NAMES = {
    "01": "AP",
    "02": "FRP",
    "03": "H",
    "04": "KRF",
    "05": "SP",
    "06": "SV",
    "07": "V",
    "08": "MDG",
    "09": "NKP",
    "10": "PP",
    "122": "DEM",
    "123": "KONS",
    "152": "INP",
    "159": "DNI",
    "55": "R",
}


def get_json(url, **params):
    data = download(url, params, 60)
    return json.loads(data.decode("utf-8"))


def download(url, params, timeout):
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}" if query else url
    try:
        with urllib.request.urlopen(full_url, timeout=timeout) as response:
            return response.read()
    except urllib.error.URLError as err:
        if "CERTIFICATE_VERIFY_FAILED" not in str(err):
            raise
        print(f"TLS certificate verification failed for {url}", file=sys.stderr)
        print("Retrying without verification", file=sys.stderr)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(
            full_url,
            timeout=timeout,
            context=context,
        ) as response:
            return response.read()


def find_dimension(meta, words):
    for did, dim in meta["dimension"].items():
        label = dim.get("label", "").lower()
        did_lower = did.lower()
        if any(w in label or w in did_lower for w in words):
            return did
    raise RuntimeError(f"Could not find dimension matching {words}")


def find_contents_code(meta):
    for did, dim in meta["dimension"].items():
        if did.lower() in ("contentscode", "contents"):
            labels = dim["category"]["label"]
            if "Godkjente1" in labels:
                return did, "Godkjente1"
            for code, label in labels.items():
                low = label.lower()
                if (
                    ("godkjende" in low and "røyster" in low)
                    or ("godkjente" in low and "stemmer" in low)
                    or ("valid" in low and "votes" in low and "cent" not in low)
                ):
                    return did, code
            return did, "*"
    raise RuntimeError("Could not find ContentsCode dimension")


def current_electoral_district_codes(meta, region_var):
    labels = meta["dimension"][region_var]["category"]["label"]
    return [
        code
        for code in DISTRICT_ORDER
        if code in labels and "(-" not in labels[code]
    ]


def numeric_votes(value):
    if value in (".", "..", "", None):
        return 0
    return int(float(str(value).replace(",", ".")))


def short_party_name(code, labels):
    if code in PARTY_NAMES:
        return PARTY_NAMES[code]
    label = labels.get(code, code)
    paren = re.search(r"\(([A-Za-z0-9ÆØÅæøå]{2,6})\)", label)
    if paren:
        return paren.group(1).upper()

    letters = re.sub(r"[^A-Za-z0-9ÆØÅæøå]+", "", label)
    return (letters[:6] or code).upper()


def write_party_abbreviations(path, parties, labels):
    abbreviations = {}
    for party_code in parties:
        short = short_party_name(party_code, labels)
        abbreviations.setdefault(short, []).append(labels.get(party_code, party_code))
    with open(path, "w", encoding="utf-8") as fd:
        for short in sorted(abbreviations):
            names = " / ".join(abbreviations[short])
            print(f"{short:<8} {names}", file=fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("positional_year", nargs="?")
    ap.add_argument("--year", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--abbr-out", default=None)
    args = ap.parse_args()
    year = args.year or args.positional_year or "2025"
    if year not in TOTAL_SEATS:
        supported_years = ", ".join(TOTAL_SEATS)
        raise ValueError(f"Seat counts are only configured for: {supported_years}")

    out = args.out or Path(__file__).resolve().parent.parent / f"norway_{year}.csv"
    abbr_out = args.abbr_out
    if not abbr_out:
        abbr_out = Path(__file__).resolve().parent / f"party-abbreviations_{year}.txt"

    meta = get_json(f"{BASE}/metadata", lang=LANG)

    time_var = find_dimension(meta, ["tid", "year", "år"])
    region_var = find_dimension(meta, ["region"])
    party_var = find_dimension(meta, ["parti", "valliste", "party"])
    contents_var, contents_code = find_contents_code(meta)
    district_codes = current_electoral_district_codes(meta, region_var)
    district_labels = meta["dimension"][region_var]["category"]["label"]
    party_labels = meta["dimension"][party_var]["category"]["label"]
    party_order = list(meta["dimension"][party_var]["category"]["index"])

    params = {
        "lang": LANG,
        f"valueCodes[{time_var}]": year,
        f"valueCodes[{region_var}]": ",".join(district_codes),
        f"valueCodes[{party_var}]": "*",
        f"valueCodes[{contents_var}]": contents_code,
        "outputFormat": "csv",
        "outputFormatParams": "SeparatorSemicolon",
    }

    data = download(f"{BASE}/data", params, 120)
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    vote_col = reader.fieldnames[-1]
    wide = {district_code: {} for district_code in district_codes}
    for row in reader:
        votes = numeric_votes(row[vote_col])
        if votes <= 0:
            continue
        wide[row[region_var]][row[party_var]] = votes

    used_parties = {party for row in wide.values() for party in row}
    parties = [code for code in party_order if code in used_parties]

    rows = []
    for district_code, party_votes in wide.items():
        total_seats = TOTAL_SEATS[year][district_code]
        row = {
            "Kjördæmi": district_labels[district_code],
            "fixed": total_seats - 1,
            "adj": 1,
        }
        for party_code in parties:
            row[short_party_name(party_code, party_labels)] = party_votes.get(
                party_code,
                0,
            )
        rows.append(row)

    party_columns = [short_party_name(code, party_labels) for code in parties]
    fieldnames = ["Kjördæmi", "fixed", "adj", *party_columns]
    with open(out, "w", encoding="utf-8", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "Kjördæmi": "Party names",
            **dict(zip(party_columns, (party_labels.get(code, code) for code in parties))),
        })
        writer.writerows(rows)
    print(f"Wrote {len(rows)} districts and {len(parties)} parties to {out}")
    write_party_abbreviations(abbr_out, parties, party_labels)
    print(f"Wrote party abbreviations to {abbr_out}")

if __name__ == "__main__":
    main()
