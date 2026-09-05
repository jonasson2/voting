#!/usr/bin/env python3
import argparse
import csv
import io
import re
import ssl
import sys
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

VOTES_2022_2018_URL = (
    "https://www.val.se/download/18.162047b519a91d05331197bd/1786611369096/"
    "slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx"
)
DETAILED_2022_URL = (
    "https://www.val.se/download/18.162047b519a91d0533118f4b/1764336897948/"
    "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-"
    "valdeltagande-riksdagsvalet-2022.xlsx"
)
DETAILED_2018_URL = (
    "https://historik.val.se/val/val2018/statistik/2018_R_per_valdistrikt.xlsx"
)
FIXED_SEATS_URL = (
    "https://www.val.se/download/18.4005a7d19dee20a8ea544/1778074856144/"
    "valkretsmandat-riksdag-1988-2026.xlsx"
)
RESULTS_2014_URL = (
    "https://historik.val.se/val/val2014/slutresultat/slutresultat.zip"
)

PARTY_NAMES = {
    "Arbetarepartiet-Socialdemokraterna": "S",
    "Centerpartiet": "C",
    "Kristdemokraterna": "KD",
    "Liberalerna (tidigare Folkpartiet)": "L",
    "Miljöpartiet de gröna": "MP",
    "Moderaterna": "M",
    "Sverigedemokraterna": "SD",
    "Vänsterpartiet": "V",
}
PARTY_LABELS = {value: key for key, value in PARTY_NAMES.items()}
XML_PARTY_NAMES = {
    "FP": "L",
}
PARTY_ORDER = ["M", "C", "L", "KD", "S", "V", "MP", "SD", "FI"]
EXCLUDED_PARTIES = {
    "Summa giltiga röster",
    "Valdeltagande",
    "blanka röster",
    "ej anmält deltagande",
    "övriga anmälda partier",
    "övriga ogiltiga",
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
        with urllib.request.urlopen(url, timeout=120, context=context) as response:
            return response.read()


def cell_column(cell_ref):
    return re.match(r"[A-Z]+", cell_ref).group(0)


def clean_name(name):
    name = re.sub(r"(?:\s+\d+\))+$", "", name)
    if name == "Kopparbergs län/Dalarnas län":
        name = "Dalarnas län"
    return name.strip()


def read_xlsx_sheet(data, sheet_index):
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        strings = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("x:si", ns):
                strings.append("".join(t.text or "" for t in item.findall(".//x:t", ns)))
        sheet = f"xl/worksheets/sheet{sheet_index}.xml"
        root = ET.fromstring(zf.read(sheet))
    rows = []
    for row in root.findall(".//x:row", ns):
        values = {}
        for cell in row.findall("x:c", ns):
            value = cell.findtext("x:v", default="", namespaces=ns)
            if cell.attrib.get("t") == "s" and value:
                value = strings[int(value)]
            values[cell_column(cell.attrib["r"])] = value
        if any(values.values()):
            rows.append(values)
    return rows


def int_value(value):
    if value in ("", None):
        return 0
    return int(float(str(value).replace(",", ".")))


def short_party_name(name, used):
    if name in PARTY_NAMES:
        return PARTY_NAMES[name]
    words = re.findall(r"[A-Za-zÅÄÖåäö0-9]+", name)
    if not words:
        base = "P"
    elif len(words) == 1:
        base = words[0][:8].upper()
    else:
        base = "".join(word[0] for word in words[:8]).upper()
    code = base
    index = 2
    while code in used:
        suffix = str(index)
        code = f"{base[:8 - len(suffix)]}{suffix}"
        index += 1
    used.add(code)
    return code


def add_votes(votes, district, party, count):
    votes.setdefault(district, OrderedDict())
    votes[district][party] = votes[district].get(party, 0) + count


def party_columns(header):
    excluded = {
        "LÄNSKOD",
        "KOMMUNKOD",
        "VALKRETSKOD",
        "VALDISTRIKTSKOD",
        "LÄNSNAMN",
        "KOMMUNNAMN",
        "VALKRETSNAMN",
        "VALDISTRIKTSNAMN",
        "OGEJ",
        "BLANK",
        "OG",
        "RÖSTER GILTIGA",
        "RÖSTANDE",
        "RÖSTBERÄTTIGADE",
        "VALDELTAGANDE",
        "ÖVR",
    }
    return [
        (col, value)
        for col, value in header.items()
        if value and value not in excluded
    ]


def fixed_seats_by_year():
    rows = read_xlsx_sheet(download(FIXED_SEATS_URL), 1)
    header = next(row for row in rows if row.get("A") == "Valkrets")
    year_cols = {value: col for col, value in header.items() if value}
    seats = {year: {} for year in year_cols if year != "Valkrets"}
    for row in rows[rows.index(header) + 1:]:
        name = clean_name(row.get("A", ""))
        if not name:
            continue
        for year, col in year_cols.items():
            if year == "Valkrets":
                continue
            value = row.get(col, "")
            if value:
                seats[year][name] = int_value(value)
    return seats


def parse_recent_votes(year, fixed):
    if year not in ("2018", "2022"):
        raise ValueError("Recent workbook only supports 2018 and 2022")
    total_seat_col = "M" if year == "2022" else "O"
    summary_rows = read_xlsx_sheet(download(VOTES_2022_2018_URL), 2)
    total_seats = {}
    for row in summary_rows:
        district = row.get("B", "")
        if row.get("L") == "Summa" and district:
            total_seats[district] = int_value(row.get(total_seat_col, ""))
    if year == "2018":
        return parse_2018_votes(fixed[year], total_seats)
    return parse_2022_votes(fixed[year], total_seats)


def parse_2018_votes(fixed, total_seats):
    rows = read_xlsx_sheet(download(DETAILED_2018_URL), 2)
    header = rows[0]
    votes = OrderedDict()
    labels = {}
    used = set()
    columns = []
    for col, party in party_columns(header):
        code = short_party_name(party, used)
        labels[code] = party
        columns.append((col, code))
    for row in rows[1:]:
        district = row.get("G", "")
        if not district:
            continue
        for col, code in columns:
            add_votes(votes, district, code, int_value(row.get(col, "")))
    parties, result_rows = build_rows(votes, fixed, total_seats)
    return parties, result_rows, labels


def parse_2022_votes(fixed, total_seats):
    rows = read_xlsx_sheet(download(DETAILED_2022_URL), 2)
    votes = OrderedDict()
    labels = {}
    used = set()
    for row in rows[1:]:
        district = row.get("I", "").strip()
        party = row.get("J", "").strip()
        if not district or not party or party in EXCLUDED_PARTIES:
            continue
        if party not in labels.values():
            code = short_party_name(party, used)
            labels[code] = party
        else:
            code = next(key for key, value in labels.items() if value == party)
        add_votes(votes, district, code, int_value(row.get("K", "")))
    parties, result_rows = build_rows(votes, fixed, total_seats)
    return parties, result_rows, labels


def parse_2014_votes():
    archive = zipfile.ZipFile(io.BytesIO(download(RESULTS_2014_URL)))
    xml = archive.read("slutresultat_00R.xml")
    root = ET.fromstring(xml)
    votes = OrderedDict()
    fixed = {}
    total_seats = {}
    labels = {}
    for party in root.iter("PARTI"):
        code = XML_PARTY_NAMES.get(
            party.attrib["FÖRKORTNING"],
            party.attrib["FÖRKORTNING"],
        )
        labels[code] = party.attrib["BETECKNING"]
    for district in root.iter("KRETS_RIKSDAG"):
        name = district.attrib["NAMN"]
        fixed[name] = int_value(district.attrib["MANDAT_VALKRETS"])
        total_seats[name] = fixed[name]
        votes[name] = {}
        for child in district:
            if child.tag == "GILTIGA":
                code = XML_PARTY_NAMES.get(child.attrib["PARTI"], child.attrib["PARTI"])
                votes[name][code] = int_value(child.attrib["RÖSTER"])
                total_seats[name] += int_value(child.attrib.get("VARAV_UTJÄMNING", "0"))
            elif child.tag == "ÖVRIGA_GILTIGA":
                for party in child:
                    if party.tag != "GILTIGA":
                        continue
                    code = XML_PARTY_NAMES.get(
                        party.attrib["PARTI"],
                        party.attrib["PARTI"],
                    )
                    votes[name][code] = int_value(party.attrib["RÖSTER"])
    parties, result_rows = build_rows(votes, fixed, total_seats)
    return parties, result_rows, labels


def build_rows(votes, fixed, total_seats):
    parties = [p for p in PARTY_ORDER if any(p in row for row in votes.values())]
    extra = sorted({p for row in votes.values() for p in row} - set(parties))
    parties.extend(extra)
    rows = []
    for district, row_votes in votes.items():
        if district not in fixed:
            raise KeyError(f"Missing fixed seats for {district}")
        total = total_seats.get(district, fixed[district])
        row = {
            "Kjördæmi": district,
            "fixed": fixed[district],
            "adj": total - fixed[district],
        }
        for party in parties:
            row[party] = row_votes.get(party, 0)
        rows.append(row)
    return parties, rows


def write_votes(year, out):
    if year == "2014":
        parties, rows, labels = parse_2014_votes()
    else:
        parties, rows, labels = parse_recent_votes(year, fixed_seats_by_year())
    fieldnames = ["Kjördæmi", "fixed", "adj", *parties]
    with open(out, "w", encoding="utf-8", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} districts and {len(parties)} parties to {out}")
    abbr_out = Path(__file__).resolve().parent / f"party-abbreviations_{year}.txt"
    with open(abbr_out, "w", encoding="utf-8") as fd:
        for party in parties:
            print(f"{party:<8} {labels.get(party, party)}", file=fd)
    print(f"Wrote party abbreviations to {abbr_out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", choices=["2014", "2018", "2022"])
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = args.out or Path(__file__).resolve().parent.parent / f"sweden_{args.year}.csv"
    write_votes(args.year, out)


if __name__ == "__main__":
    main()
