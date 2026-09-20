#!/usr/bin/env python3
"""Prepare Danish votes and official seat allocations for simulator testing."""

import argparse
import csv
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


HERE = Path(__file__).resolve().parent
ELECTIONS = {
    "2019": {
        "base_url": "https://www.dst.dk/valg/Valg1684447/valgopg/",
        "date": "2019-06-05",
        "seat_allocation_url": (
            "https://www.dst.dk/valg/Valg1684447/other/Folketingsvalg2019_v5.pdf"),
        "fixed_seats": {
            "Københavns Storkreds": 16,
            "Københavns Omegns Storkreds": 11,
            "Nordsjællands Storkreds": 10,
            "Bornholms Storkreds": 2,
            "Sjællands Storkreds": 20,
            "Fyns Storkreds": 12,
            "Sydjyllands Storkreds": 18,
            "Østjyllands Storkreds": 18,
            "Vestjyllands Storkreds": 13,
            "Nordjyllands Storkreds": 15,
        },
        "region_adjustment_seats": {"H": 11, "SS": 15, "MN": 14},
    },
    "2022": {
        "base_url": "https://www.dst.dk/valg/Valg1968094/valgopg/",
        "date": "2022-11-01",
        "seat_allocation_url": (
            "https://www.dst.dk/valg/Valg1968094/other/"
            "Fordelingen-af-mandater-ved-FV2022.pdf"),
        "fixed_seats": {
            "Københavns Storkreds": 17,
            "Københavns Omegns Storkreds": 11,
            "Nordsjællands Storkreds": 10,
            "Bornholms Storkreds": 2,
            "Sjællands Storkreds": 20,
            "Fyns Storkreds": 12,
            "Sydjyllands Storkreds": 17,
            "Østjyllands Storkreds": 18,
            "Vestjyllands Storkreds": 13,
            "Nordjyllands Storkreds": 15,
        },
        "region_adjustment_seats": {"H": 11, "SS": 15, "MN": 14},
    },
    "2026": {
        "base_url": "https://www.dst.dk/valg/Valg2546527/valgopg/",
        "date": "2026-03-24",
        "report_url": (
            "https://www.valg.im.dk/Media/639117581241830159/"
            "Danmarks%20Statistiks%20opgrelse%20af%20folketingsvalget%20den%2024."
            "%20marts%202026.pdf"
        ),
    },
}
REGION_CODES = ["H", "SS", "MN"]
INDEPENDENTS = "Uden for partierne"
VALID_VOTES = "I alt gyldige stemmer"


class ResultPage(HTMLParser):
    """Read the result tables and navigation links, ignoring layout tables."""

    def __init__(self, html):
        super().__init__()
        self.links = {}
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("title") and attrs.get("href"):
            self.links[attrs["href"]] = attrs["title"]
        if tag == "table" and attrs.get("class") == "valgopg_tabel":
            self.table = []
        elif self.table is not None:
            if tag == "tr":
                self.row = []
                self.cell = None
            elif tag == "td":
                self.cell = {"class": attrs.get("class", ""), "text": ""}
                self.row.append(self.cell)
            elif tag == "br" and self.cell is not None:
                self.cell["text"] += " "

    def handle_endtag(self, tag):
        if self.table is not None:
            if tag == "table":
                self.tables.append(self.table)
                self.table = self.row = self.cell = None
            elif tag == "tr":
                self.table.append(self.row)
                self.row = self.cell = None
            elif tag == "td":
                self.cell = None

    def handle_data(self, text):
        if self.cell is not None:
            self.cell["text"] += text


def integer(text):
    text = text.strip()
    if text == "-":
        return 0
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{3})*", text):
        raise ValueError(f"Invalid count in official result: {text!r}")
    return int(text.replace(".", ""))


def download(url, path, refresh=False):
    if refresh or not path.exists():
        print(f"Downloading {url}", flush=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            content = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return path.read_bytes()


def load_page(base_url, raw_directory, filename, refresh):
    content = download(base_url + filename, raw_directory / filename, refresh)
    return ResultPage(content.decode("utf-8-sig"))


def result(page, name, filename, base_url=""):
    parties = {}
    valid_votes = None
    if not page.tables:
        raise ValueError(f"No result table in {filename}")
    headers = ["".join(c["text"].split()).replace("-", "")
               for c in page.tables[0][1]]
    fixed_only = headers == ["Parti", "Antal", "Pct.", "Kredsmandater", ""]
    votes_only = (headers[:3] == ["Parti", "Antal", "Pct."]
                  and not any(headers[3:]))
    if not fixed_only and not votes_only and headers != [
            "Parti", "Antal", "Pct.", "Mandater", "Kredsmandater", "Till\u00e6gsmandater"]:
        raise ValueError(f"Unknown result-table headings in {filename}: {headers}")
    for row in page.tables[0]:
        cells = [cell["text"].strip() for cell in row]
        if not cells or row[0]["class"] != "vaelgeropg_parti":
            continue
        if cells[0] == VALID_VOTES:
            valid_votes = integer(cells[1])
        result_columns = 3 if votes_only else len(headers)
        if len(cells) < result_columns or any(cells[result_columns:]):
            continue
        cells = cells[:result_columns]
        label = cells[0]
        if label in parties:
            raise ValueError(f"Duplicate party {label} in {filename}")
        parties[label] = {
            "votes": integer(cells[1]),
            "total_seats": 0 if votes_only else integer(cells[3]),
            "fixed_seats": 0 if votes_only else integer(
                cells[3] if fixed_only else cells[4]),
            "adjustment_seats": 0 if votes_only or fixed_only else integer(cells[5]),
        }
        seats = parties[label]
        if seats["total_seats"] != seats["fixed_seats"] + seats["adjustment_seats"]:
            raise ValueError(f"Inconsistent seats for {label} in {filename}")
    parties.setdefault(INDEPENDENTS, {
        "votes": 0, "total_seats": 0, "fixed_seats": 0, "adjustment_seats": 0,
    })
    if valid_votes is None or sum(p["votes"] for p in parties.values()) != valid_votes:
        raise ValueError(f"Votes do not sum to valid votes in {filename}")
    return {"name": name, "source": base_url + filename,
            "valid_votes": valid_votes, "parties": parties}


def independent_candidates(page, district):
    candidates = {}
    if len(page.tables) != 2:
        raise ValueError(f"Expected party and candidate tables in {district['name']}")
    for row in page.tables[1]:
        values = [cell["text"].strip() for cell in row[1:] if cell["text"].strip()]
        if row[0]["class"] == "vaelgeropg_parti" and values:
            name = row[0]["text"].strip()
            if name in candidates:
                raise ValueError(f"Duplicate independent candidate: {name}")
            candidates[name] = integer(values[-1])
    official = district["parties"][INDEPENDENTS]
    if sum(candidates.values()) != official["votes"]:
        raise ValueError(f"Independent votes do not reconcile in {district['name']}")
    # These pages give seats only for the combined independent category.
    if official["total_seats"]:
        raise ValueError("Individual independent seat results need to be obtained")
    return candidates


def reconcile(parent, children):
    for child in children:
        if child["parties"].keys() != parent["parties"].keys():
            raise ValueError(f"Party labels differ in {child['name']}")
    for party, values in parent["parties"].items():
        for field, expected in values.items():
            actual = sum(child["parties"][party][field] for child in children)
            if actual != expected:
                raise ValueError(
                    f"{parent['name']}: {party} {field}: {actual} != {expected}")


def collect(year, refresh=False):
    election = ELECTIONS[year]
    base_url = election["base_url"]
    raw_directory = HERE / "raw" / year
    index = load_page(base_url, raw_directory, "valgopg.htm", refresh)
    national = result(
        load_page(base_url, raw_directory, "valgopgHL.htm", refresh),
        "Danmark", "valgopgHL.htm", base_url)
    region_links = [(url, name) for url, name in index.links.items()
                    if re.fullmatch(r"valgopgLand\d+\.htm", url)]
    if len(region_links) != 3:
        raise ValueError("Expected three Danish regions")
    regions, districts = [], []
    for code, (filename, name) in zip(REGION_CODES, region_links):
        page = load_page(base_url, raw_directory, filename, refresh)
        region = result(page, name, filename, base_url)
        region["abbreviation"] = code
        region_districts = []
        for filename, name in page.links.items():
            if not re.fullmatch(r"valgopgStor\d+\.htm", filename):
                continue
            district_page = load_page(base_url, raw_directory, filename, refresh)
            district = result(district_page, name, filename, base_url)
            district["region"] = code
            district["independent_candidates"] = independent_candidates(
                district_page, district)
            region_districts.append(district)
        if len(region_districts) != (4 if code == "H" else 3):
            raise ValueError(f"Unexpected constituency count in {name}")
        reconcile(region, region_districts)
        regions.append(region)
        districts.extend(region_districts)
    if "fixed_seats" in election:
        for district in districts:
            district["num_fixed_seats"] = election["fixed_seats"][district["name"]]
        for region in regions:
            region["num_adj_seats"] = election["region_adjustment_seats"][
                region["abbreviation"]]
    reconcile(national, regions)
    if len({d["source"] for d in districts}) != 10:
        raise ValueError("Expected ten distinct constituencies")
    fixed_count = sum(
        district.get("num_fixed_seats", sum(
            party["fixed_seats"] for party in district["parties"].values()))
        for district in districts)
    adjustment_count = sum(
        region.get("num_adj_seats", sum(
            party["adjustment_seats"] for party in region["parties"].values()))
        for region in regions)
    if fixed_count != 135:
        raise ValueError("Expected 135 fixed seats")
    if adjustment_count != 40:
        raise ValueError("Expected 40 adjustment seats")
    return {"election_date": election["date"],
            "seat_allocation_source": election.get("seat_allocation_url"),
            "national": national,
            "regions": regions, "constituencies": districts}


def write_votes(official, output):
    party_labels = [p for p in official["national"]["parties"] if p != INDEPENDENTS]
    parties = [label.split(". ", 1) for label in party_labels]
    independent = [(d["name"], name) for d in official["constituencies"]
                   for name in d["independent_candidates"]]
    abbreviations = [p[0] for p in parties] + [f"U{i+1}" for i in range(len(independent))]
    names = [p[1] for p in parties] + [name for _, name in independent]
    year = official["election_date"][:4]
    max_adjustment = sum(
        region.get("num_adj_seats", sum(
            party["adjustment_seats"] for party in region["parties"].values()))
        for region in official["regions"])
    header = [f"Denmark {year}", "fixed", "min_adj", "max_adj", "region", *abbreviations]
    rows = [header,
            ["Party names", "", "", "", "", *names],
            ["Independent candidates", "", "", "", "",
             *([0] * len(parties)), *([1] * len(independent))],
            ["Max adj seats", "", "", max_adjustment]]
    for district in official["constituencies"]:
        votes = [district["parties"][label]["votes"] for label in party_labels]
        votes += [district["independent_candidates"].get(name, 0)
                  if district["name"] == home else 0 for home, name in independent]
        if sum(votes) != district["valid_votes"]:
            raise ValueError(f"Output vote total differs in {district['name']}")
        fixed = district.get("num_fixed_seats", sum(
            party["fixed_seats"] for party in district["parties"].values()))
        rows.append([district["name"], fixed, 0, "-", district["region"], *votes])
    rows.extend([[], ["Regions", "Name", "adj"]])
    for region in official["regions"]:
        adjustment = region.get("num_adj_seats", sum(
            party["adjustment_seats"] for party in region["parties"].values()))
        rows.append([region["abbreviation"], region["name"], adjustment])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        for row in rows:
            writer.writerow(row + [""] * (len(header) - len(row)))
    with output.open(encoding="utf-8", newline="") as file:
        reread = list(csv.reader(file))
    if any(len(row) != len(header) for row in reread):
        raise ValueError("Output rows have inconsistent widths")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", choices=sorted(ELECTIONS))
    parser.add_argument("--refresh", action="store_true", help="Download cached sources again")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = args.out or HERE.parent / f"denmark_{args.year}.csv"
    official = collect(args.year, args.refresh)
    report_url = ELECTIONS[args.year].get("report_url")
    if report_url:
        download(report_url, HERE / "raw" / args.year / "official-calculation.pdf",
                 args.refresh)
    seat_allocation_url = ELECTIONS[args.year].get("seat_allocation_url")
    if seat_allocation_url:
        download(seat_allocation_url, HERE / "raw" / args.year / "seat-allocation.pdf",
                 args.refresh)
    write_votes(official, output)
    expected = HERE / f"official-results_{args.year}.json"
    expected.write_text(json.dumps(official, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {expected}")
    print(f"Verified {official['national']['valid_votes']:,} votes, 135 fixed seats and 40 adjustment seats")
    print("Regional and constituency totals match the official national result")


if __name__ == "__main__":
    main()
