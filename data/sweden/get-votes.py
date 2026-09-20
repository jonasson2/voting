#!/usr/bin/env python3
import argparse
import csv
import io
import json
import re
import ssl
import sys
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from html.parser import HTMLParser
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
RESULTS_2026_URL = (
    "https://resultat.val.se/data/resultat/val2026/RD_S.json"
)
RESULTS_2014_INDEX_URL = (
    "https://historik.val.se/val/val2014/slutresultat/R/rike/index.html"
)
RESULTS_2014_DISTRICT_URL = (
    "https://historik.val.se/val/val2014/slutresultat/R/rvalkrets/{code}/"
    "index.html"
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
PARTY_LABELS_2018 = {
    **PARTY_LABELS,
    "FI": "Feministiskt initiativ",
    "AFS": "Alternativ för Sverige",
    "BASIP": "Basinkomstpartiet",
    "CSIS": "Common sense in Sweden",
    "DD": "Direktdemokraterna",
    "DJUP": "Djurens parti",
    "EAP": "Europeiska Arbetarpartiet-EAP",
    "ENH": "Enhet",
    "FHS": "Folkhemmet Sverige",
    "GUP": "Gula Partiet",
    "INI": "Initiativet",
    "KLP": "Klassiskt liberala partiet",
    "KRVP": "Kristna Värdepartiet",
    "LPO": "Landsbygdspartiet Oberoende",
    "MED": "Medborgerlig Samling",
    "NMR": "Nordiska motståndsrörelsen",
    "NORRP": "Norrlandspartiet",
    "NYREF": "NY REFORM",
    "PP": "Piratpartiet",
    "RNP": "Reformist Neutral Partiet",
    "S-FRP": "Sverige ut ur EU/Frihetliga Rättvisepartiet (FRP)",
    "SKP": "Sveriges Kommunistiska Parti (SKP)",
    "SKÅ": "SKÅNEPARTIET",
    "TRP": "TRYGGHETSPARTIET",
    "VL-S": "Vårt land - Sverige",
}
XML_PARTY_NAMES = {
    "FP": "L",
}
PARTY_ORDER = ["M", "C", "L", "KD", "S", "V", "MP", "SD", "FI"]
# Preserve the constituency order of the discontinued 2014 XML source.
DISTRICT_ORDER_2014 = [
    "10", "24", "09", "25", "15", "27", "06", "08", "07", "29",
    "11", "14", "13", "12", "01", "02", "04", "03", "21", "28",
    "26", "23", "16", "18", "19", "17", "20", "22", "05",
]
# The 2014 HTML tables omit abbreviations for these registered parties.
PARTY_CODES_2014 = {
    "Republikanerna": "0020",
    "Sverige ut ur EU / Frihetliga Rättvisepartiet (FRP)": "0675",
    "Framstegspartiet": "1146",
    "Direktdemokraterna": "1170",
    "Fredsdemokraterna": "1177",
    "Nya Partiet": "1195",
    "Hälsopartiet": "1270",
}
EXCLUDED_PARTIES = {
    "Summa giltiga röster",
    "Valdeltagande",
    "blanka röster",
    "ej anmält deltagande",
    "övriga anmälda partier",
    "övriga ogiltiga",
}


class HtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


class DistrictLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.districts = OrderedDict()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attributes = dict(attrs)
        title = attributes.get("title", "")
        href = attributes.get("href", "")
        match = re.search(r"/rvalkrets/(\d+)/index\.html$", href)
        prefix = "Riksdagsvalkrets "
        if match and title.startswith(prefix):
            self.districts.setdefault(match.group(1), title[len(prefix):])


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
        labels[code] = PARTY_LABELS_2018.get(party.upper(), party)
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


def parse_2026_votes(fixed):
    result = json.loads(download(RESULTS_2026_URL))
    votes = OrderedDict()
    labels = {}
    pruned = {}
    for constituency in result["valkretsar"]:
        district = constituency["namn"]
        votes[district] = OrderedDict()
        pruned[district] = 0
        for party in constituency["rosterPaverkaMandat"]["partiroster"]:
            if party["visa"] == 0:
                code = party["partiforkortning"]
                votes[district][code] = party["antalRoster"]
                labels[code] = party["partibeteckning"]
            elif party["visa"] == 2:
                pruned[district] += party["antalRoster"]
    parties, result_rows = build_rows(votes, fixed, fixed)
    for row in result_rows:
        row["Pruned"] = pruned[row["Kjördæmi"]]
    return parties, result_rows, labels


def parse_2014_votes():
    index = download(RESULTS_2014_INDEX_URL).decode("iso-8859-1")
    link_parser = DistrictLinkParser()
    link_parser.feed(index)
    if len(link_parser.districts) != 29:
        raise RuntimeError(
            f"Expected 29 constituencies, found {len(link_parser.districts)}"
        )

    votes = OrderedDict()
    labels = {}
    for district_code in DISTRICT_ORDER_2014:
        name = link_parser.districts[district_code]
        url = RESULTS_2014_DISTRICT_URL.format(code=district_code)
        page = download(url).decode("iso-8859-1")
        table_parser = HtmlTableParser()
        table_parser.feed(page)
        votes[name] = {}
        for table in table_parser.tables:
            if not table or table[0][:2] != ["Förk.", "Parti"]:
                continue
            for row in table[1:]:
                if len(row) < 3 or not row[2].isdigit():
                    continue
                code = row[0] or PARTY_CODES_2014.get(row[1])
                if code in {None, "ÖVR", "BLANK", "OG", "VDT"}:
                    continue
                code = XML_PARTY_NAMES.get(code, code)
                labels[code] = row[1]
                votes[name][code] = int(row[2])

    fixed = fixed_seats_by_year()["2014"]
    parties, result_rows = build_rows(votes, fixed, fixed)
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
        max_total_adj_seats = 39
    elif year == "2026":
        parties, rows, labels = parse_2026_votes(fixed_seats_by_year()[year])
        max_total_adj_seats = 39
    else:
        parties, rows, labels = parse_recent_votes(year, fixed_seats_by_year())
        max_total_adj_seats = sum(row["adj"] for row in rows)
    for row in rows:
        row["min_adj"] = 0
        row["max_adj"] = "-"
        del row["adj"]
    has_pruned = year == "2026"
    fieldnames = ["Kjördæmi", "fixed", "min_adj", "max_adj", *parties]
    if has_pruned:
        fieldnames.append("Pruned")
    with open(out, "w", encoding="utf-8", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "Kjördæmi": "Party names",
            **{party: labels.get(party, party) for party in parties},
        })
        writer.writerow({
            "Kjördæmi": "Max adj seats",
            "max_adj": max_total_adj_seats,
        })
        writer.writerows(rows)
    print(f"Wrote {len(rows)} districts and {len(parties)} parties to {out}")
    abbr_out = Path(__file__).resolve().parent / f"party-abbreviations_{year}.txt"
    with open(abbr_out, "w", encoding="utf-8") as fd:
        for party in parties:
            print(f"{party:<8} {labels.get(party, party)}", file=fd)
    print(f"Wrote party abbreviations to {abbr_out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", choices=["2014", "2018", "2022", "2026"])
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = args.out or Path(__file__).resolve().parent.parent / f"sweden_{args.year}.csv"
    write_votes(args.year, out)


if __name__ == "__main__":
    main()
