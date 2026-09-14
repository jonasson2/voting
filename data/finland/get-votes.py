#!/usr/bin/env python3
import argparse
import csv
import io
import re
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path


RESULT_URLS = {
    "2019": (
        "https://tulospalvelu.vaalit.fi/EKV-2019/"
        "ekv-2019_puo_maa.csv.zip"
    ),
    "2023": (
        "https://tulospalvelu.vaalit.fi/EKV-2023/"
        "ekv-2023_puo_maa.csv.zip"
    ),
}
CONSTITUENCY_NAMES = {
    "01": "Helsinki",
    "02": "Uusimaa",
    "03": "Varsinais-Suomi",
    "04": "Satakunta",
    "05": "Åland",
    "06": "Häme",
    "07": "Pirkanmaa",
    "08": "Kaakkois-Suomi",
    "09": "Savo-Karjala",
    "10": "Vaasa",
    "11": "Keski-Suomi",
    "12": "Oulu",
    "13": "Lappi",
}


def download(url):
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            return response.read()
    except urllib.error.URLError as err:
        if "CERTIFICATE_VERIFY_FAILED" not in str(err):
            raise
        print(f"TLS certificate verification failed for {url}", file=sys.stderr)
        print("Retrying without verification", file=sys.stderr)
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(
            url,
            timeout=120,
            context=context,
        ) as response:
            return response.read()


def parse_result_file(year):
    archive = zipfile.ZipFile(io.BytesIO(download(RESULT_URLS[year])))
    filenames = [name for name in archive.namelist() if name.endswith(".csv")]
    if len(filenames) != 1:
        raise RuntimeError("Expected one CSV file in the result archive")
    text = archive.read(filenames[0]).decode("iso-8859-1")

    constituencies = {}
    party_names = {}
    for row in csv.reader(io.StringIO(text), delimiter=";"):
        row = [value.strip() for value in row]
        if len(row) < 45 or row[3] != "V":
            continue

        district_code = row[1]
        district = constituencies.setdefault(
            district_code,
            {
                "name": CONSTITUENCY_NAMES[district_code],
                "votes": defaultdict(int),
                "official_seats": defaultdict(int),
            },
        )

        code = row[10]
        name = row[15]
        if year == "2019" and re.search(r"Liike\s*Nyt", name, re.I):
            code, name = "LIIKE", "Liike Nyt"
        elif year == "2023" and code == "LIIK":
            code = "LIIKE"
        elif row[8] == "99":
            # Constituency associations are local, even when abbreviations repeat.
            code = f"{district_code}-{code}"

        district["votes"][code] += int(row[40])
        district["official_seats"][code] += int(row[44])
        party_names[code] = name

    if sorted(constituencies) != [f"{number:02}" for number in range(1, 14)]:
        raise RuntimeError("The result file does not contain all 13 constituencies")
    return constituencies, party_names


def dhondt(votes, num_seats):
    quotients = sorted(
        (
            (party_votes / divisor, party)
            for party, party_votes in votes.items()
            for divisor in range(1, num_seats + 1)
        ),
        reverse=True,
    )
    allocation = defaultdict(int)
    for _, party in quotients[:num_seats]:
        allocation[party] += 1
    return allocation


def validate_allocation(constituencies):
    total_seats = 0
    for district in constituencies.values():
        official = district["official_seats"]
        num_seats = sum(official.values())
        calculated = dhondt(district["votes"], num_seats)
        parties = set(official) | set(calculated)
        differences = {
            party: (calculated[party], official[party])
            for party in parties
            if calculated[party] != official[party]
        }
        if differences:
            raise RuntimeError(
                f"D'Hondt does not reproduce {district['name']}: {differences}"
            )
        total_seats += num_seats
    if total_seats != 200:
        raise RuntimeError(f"Expected 200 seats, found {total_seats}")


def write_votes(year, out):
    constituencies, party_names = parse_result_file(year)
    validate_allocation(constituencies)

    national_votes = defaultdict(int)
    for district in constituencies.values():
        for party, votes in district["votes"].items():
            national_votes[party] += votes
    parties = sorted(party_names, key=lambda party: (-national_votes[party], party))

    fieldnames = ["Kjördæmi", "fixed", "adj", *parties]
    with open(out, "w", encoding="utf-8", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "Kjördæmi": "Party names",
            **{party: party_names[party] for party in parties},
        })
        for district_code in sorted(constituencies):
            district = constituencies[district_code]
            writer.writerow({
                "Kjördæmi": district["name"],
                "fixed": sum(district["official_seats"].values()),
                "adj": 0,
                **{
                    party: district["votes"].get(party, 0)
                    for party in parties
                },
            })

    print(
        f"Wrote {len(constituencies)} constituencies and "
        f"{len(parties)} lists to {out}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", choices=RESULT_URLS)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = args.out or Path(__file__).resolve().parent.parent / f"finland_{args.year}.csv"
    write_votes(args.year, out)


if __name__ == "__main__":
    main()
