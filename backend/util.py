#coding:utf-8
import random
import csv
import sys #??????
from tabulate import tabulate
import io
import os
import configparser
import codecs
from distutils.util import strtobool
from traceback import format_exc

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text

def sum_abs_diff(a, b):  # Compute sum of absolute values of a minus b
    if shape(a) != shape(b):
        return None
    s = 0
    if isinstance(a[0],list):
        for (rowa,rowb) in zip(a,b):
            s += sum(abs(x-y) for (x,y) in zip(rowa,rowb))
    else:
        s += sum(abs(x-y) for (x,y) in zip(a,b))
    return s

def shape(M):
    # Simply assume that all rows have equal length
    if not isinstance(M,list): return None
    if not isinstance(M[0],list): return len(M)
    return (len(M),len(M[0]))

#??????
def random_id(length=8):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    s = "".join(random.sample(chars, length))
    return s

def subtract_m(A, B):
    C = []
    for (a,b) in zip(A, B):
        c = [x - y for (x,y) in zip(a,b)]
        C.append(c)
    return C

def read_csv(filename):
    with io.open(filename, mode="r", newline='', encoding='utf-8') as f:
        for row in csv.reader(f, skipinitialspace=True):
            yield [cell for cell in row]

def read_xlsx(filename):
    import openpyxl
    book = openpyxl.load_workbook(filename)
    sheet = book.active
    for row in sheet.rows:
        yield [cell.value for cell in row]

# def load_constituencies(confile):
#     """Load constituencies from a file."""
#     if confile.endswith("csv"):
#         reader = read_csv(confile)
#     else:
#         reader = read_xlsx(confile)
#     cons = []
#     for row in reader:
#         try:
#             assert(int(row[1]) + int(row[2]) > 0)
#         except Exception as e:
#             print(row[1:3])
#             raise Exception("Error loading constituency file: "
#                             "constituency seats and adjustment seats "
#                             "must add to a nonzero number.")
#         cons.append({
#             "name": row[0],
#             "num_const_seats": int(row[1]),
#             "num_adj_seats": int(row[2])})
#     return cons

def isint(L):
    def ok(x):
        return isinstance(x,int) and x >= 0 or x.isdigit and x.isascii
    return all(ok(x) for x in L)

def load_votes_from_excel(stream, filename):
    lines = []
    if not hasattr(stream, "seekable") and hasattr(stream, "_file"):
        stream.seekable = stream._file.seekable
        # TODO: Remove this monkeypatch once this issue has been resolved.
    import openpyxl
    book = openpyxl.load_workbook(stream)
    sheet = book.active
    for row in sheet.rows:
        lines.append([cell.value for cell in row])
    return lines

def parse_input(rows, const_seats_included, adj_seats_included, filename=''):
    name_included = rows[0][0].lower() != u"kjördæmi" if rows[0][0] else False
    res = {}
    start_col = 1
    if const_seats_included:
        const_col = start_col
        start_col += 1
    if adj_seats_included:
        adj_col = start_col
        start_col += 1

    res["votes"] = [[parsint(v) for v in row[start_col:]]
                    for row in rows[1:]]

    res["parties"] = rows[0][start_col:]
    num_parties = len(res["parties"])

    res["constituencies"] = [{
        "name": row[0],
        "num_const_seats": parsint(row[const_col]) if const_seats_included else 0,
        "num_adj_seats": parsint(row[adj_col]) if adj_seats_included else 0,
    } for row in rows[1:]]

    table_name = rows[0][0] if name_included else ''
    res["name"] = determine_table_name(table_name,filename)

    return res

def check_votes(rows, filename):
    n = [len(row) for row in rows]
    if min(n) < max(n):
        return 'Not all rows have equal length'
    n = n[0]
    if n < 2:
        return 'Fewer than two columns'
    elif len(rows) < 2:
        return 'Only one row'
    toprow = rows[0]
    const_seats_incl = toprow[1].lower() == "cons"
    expected = 2 if const_seats_incl else 1
    adj_seats_incl = toprow[expected].lower() == "adj"
    skip = 1 + const_seats_incl + adj_seats_incl
    votes = [row[skip:] for row in rows[1:]]
    if not all(toprow[skip:]):
        return 'Some party names are blank'
    if not all(l[0] for l in rows[1:]):
        return 'Some constituency names are blank'
    if not all(isint(row) for row in votes):
        return 'All votes must be nonnegative integer numbers'

    result = parse_input(rows, const_seats_incl, adj_seats_incl, filename)
    return result

def parsint(value):
    return int(value) if value else 0

def determine_table_name(first,filename):
    return first if first else os.path.basename(os.path.splitext(filename)[0])

# def load_votes(votefile, consts):
#     """Load votes from a file."""
#     if votefile.endswith("csv"):
#         reader = read_csv(votefile)
#     else:
#         reader = read_xlsx(votefile)
#     parties = next(reader)[3:]
#     votes = [[] for i in range(len(consts))]
#     c_names = [x["name"] for x in consts]

#     for row in reader:
#         try:
#             v = votes[c_names.index(row[0])]
#         except:
#             print(row)
#             raise Exception("Constituency '%s' not found in constituency file"
#                             % row[0])
#         for x in row[3:]:
#             try:
#                 r = float(x)
#             except:
#                 r = 0
#             v.append(r)

#     return parties, votes

def print_table(data, header, labels, output, f_string=None):
    """
    Print 'data' in a table with 'header' and rows labelled with 'labels'.
    """
    if f_string:
        data = [[f_string.format(d) if d!=None else d for d in row] for row in data]
    data = [[labels[i]] + data[i] for i in range(len(data))]
    data = [[d if d != 0 and d != "0.0%" else None for d in row]
                for row in data]
    print(tabulate(data, header, output))

def print_steps_election(election):
    """Print detailed information about a single election."""
    systems = election.system
    out = systems["output"]
    header = ["Constituency"]
    header.extend(systems["parties"])
    header.append("Total")
    if "constituencies" in systems:
        const_names = [c["name"] for c in systems["constituencies"]]
    else:
        const_names = systems["constituency_names"]
    const_names.append("Total")

    print("Votes")
    xtd_votes = add_totals(election.m_votes)
    print_table(xtd_votes, header, const_names, out)

    print("\nVote shares")
    xtd_shares = find_xtd_shares(xtd_votes)
    print_table(xtd_shares, header, const_names, out, "{:.1%}")

    print("\nConstituency seats")
    xtd_const_seats = add_totals(election.m_const_seats)
    print_table(xtd_const_seats, header, const_names, out)

    print("\nAdjustment seat apportionment")
    print("Threshold: {:.1%}".format(systems["adjustment_threshold"]*0.01))
    v_votes = election.v_votes
    v_votes.append(sum(election.v_votes))
    v_elim_votes = election.v_votes_eliminated
    v_elim_votes.append(sum(election.v_votes_eliminated))
    v_elim_shares = ["{:.1%}".format(v/v_elim_votes[-1])
                        for v in v_elim_votes]
    v_const_seats = election.v_const_seats_alloc
    v_const_seats.append(sum(election.v_const_seats_alloc))
    data = [v_votes, v_elim_votes, v_elim_shares, v_const_seats]
    labels = ["Total votes", "Votes above threshold",
              "Vote shares above threshold", "Constituency seats"]
    print_table(data, header[1:], labels, out)

    table = election.demonstration_table
    print("")
    print(tabulate(table["steps"], table["headers"], out))
    print("")

    xtd_total_seats = add_totals(election.results)
    print("\nAdjustment seats")
    xtd_adj_seats = matrix_subtraction(xtd_total_seats, xtd_const_seats)
    print_table(xtd_adj_seats, header, const_names, out)

    print("\nTotal seats")
    print_table(xtd_total_seats, header, const_names, out)

    print("\nSeat shares")
    xtd_shares = find_xtd_shares(xtd_total_seats)
    print_table(xtd_shares, header, const_names, out, "{:.1%}")

def pretty_print_election(election):
    """Print results of a single election."""
    systems = election.system
    header = ["Constituency"]
    header.extend(systems["parties"])
    header.append("Total")
    if "constituencies" in systems:
        const_names = [c["name"] for c in systems["constituencies"]]
    else:
        const_names = systems["constituency_names"]
    const_names.append("Total")
    xtd_results = add_totals(election.results)
    print_table(xtd_results, header, const_names, systems["output"])

def sim_election_rules(rs, test_method):
    """Get preset election systems for simulation from file."""
    config = configparser.ConfigParser()
    config.read("../data/presets/methods.ini")

    if test_method in config:
        rs.update(config[test_method])
    else:
        raise ValueError("%s is not a known apportionment method"
                            % test_method)
    rs["adjustment_threshold"] = float(rs["adjustment_threshold"])

    return rs

def hms(sec):
    # Turn seconds into xxx days hh:mm:ss
    sec = round(sec)
    minute = sec//60
    sec %= 60
    hr = minute//60
    minute %= 60
    d = hr//24
    hr %= 24
    s = f"{minute:02}:{sec:02}"
    if hr > 0:
        s = f"{hr:02}" + s
    if d == 1:
        s = "1 day + " + s
    elif d > 1:
        s = f"{d} days + " + s
    return s

def print_simulation(simulation):
    """Print detailed information about a simulation."""
    for r in range(len(simulation.system)):
        systems = simulation.system[r]
        out = systems["output"]
        print("==========================================")
        print("Adjustment method:", systems["adjustment_method"])
        print("==========================================\n")
        h = ["Constituency"]
        h.extend(systems["parties"]+["Total"])
        if "constituencies" in systems:
            const_names = [c["name"] for c in systems["constituencies"]]
        else:
            const_names = systems["constituency_names"]
        const_names.append("Total")

        print("Reference")

        print("\nVotes")
        print_table(simulation.xtd_votes, h, const_names, out)

        print("\nVote shares")
        print_table(simulation.xtd_vote_shares,
                    h, const_names, out, "{:.1%}")

        print("\nConstituency seats")
        print_table(simulation.base_allocations[r]["xtd_const_seats"],
                    h, const_names, out)

        print("\nAdjustment seats")
        print_table(simulation.base_allocations[r]["xtd_adj_seats"],
                    h, const_names, out)

        print("\nTotal seats")
        print_table(simulation.base_allocations[r]["xtd_total_seats"],
                    h, const_names, out)

        print("\nSeat shares")
        print_table(simulation.base_allocations[r]["xtd_seat_shares"],
                    h, const_names, out, "{:.1%}")

        print("\nAverages from simulation")

        print("\nVotes")
        print_table(simulation.list_data[-1]["sim_votes"]["avg"],
                    h, const_names, out)

        print("\nVote shares")
        print_table(simulation.list_data[-1]["sim_shares"]["avg"],
                    h, const_names, out, "{:.1%}")

        print("\nConstituency seats")
        print_table(simulation.list_data[r]["const_seats"]["avg"],
                    h, const_names, out)

        print("\nAdjustment seats")
        print_table(simulation.list_data[r]["adj_seats"]["avg"],
                    h, const_names, out)

        print("\nTotal seats")
        print_table(simulation.list_data[r]["total_seats"]["avg"],
                    h, const_names, out)

        print("\nSeat shares")
        print_table(simulation.list_data[r]["seat_shares"]["avg"],
                    h, const_names, out, "{:.1%}")

        print("\nStandard errors from simulation")

        print("\nVotes")
        print_table(simulation.list_data[-1]["sim_votes"]["std"],
                    h, const_names, out, "{:.3f}")

        print("\nVote shares")
        print_table(simulation.list_data[-1]["sim_shares"]["std"],
                    h, const_names, out, "{:.1%}")

        print("\nConstituency seats")
        print_table(simulation.list_data[r]["const_seats"]["std"],
                    h, const_names, out, "{:.3f}")

        print("\nAdjustment seats")
        print_table(simulation.list_data[r]["adj_seats"]["std"],
                    h, const_names, out, "{:.3f}")

        print("\nTotal seats")
        print_table(simulation.list_data[r]["total_seats"]["std"],
                    h, const_names, out, "{:.3f}")

        print("\nSeat shares")
        print_table(simulation.list_data[r]["seat_shares"]["std"],
                    h, const_names, out, "{:.1%}")

        #print("\nVotes added to change results")
        #print_table(simulation.votes_to_change, h[:-1], const_names[:-1], out)

def disp(title, value=[]):
    if not value:
        value = title
        title=''
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=80).pprint
    if title:
        print("\n" + title.upper() + ":")
    pp(value)

def dispv(title, value=None, ndec=3):
    import numpy as np
    if value is None:
        value = title
        title=''
    if title:
        print("\n" + title.upper() + ":")
    np.set_printoptions(suppress=True, precision=ndec, floatmode="fixed",
                        linewidth=120)
    print(np.array(value))
    
def short_traceback(trace):
    from pathlib import Path
    def traceline(line):
        word = line.split()
        file = remove_suffix(remove_prefix(word[1], '"'), '",')
        file = Path(file).name
        lineno = remove_suffix(word[3], ',')
        function = word[5]
        return f"{function}, {file} line {lineno}"
        
    trace = trace.splitlines()
    first = traceline(trace[1])
    last = traceline(trace[-3])
    error = trace[-1]
    # print("trace=", trace)
    return f"Server error ({first},..., {last}):\n{error}"

def writecsv(file, L):
    # Writes list of lists L to csv-file
    import csv
    with open(file, "w") as f:
        writer = csv.writer(f)
        writer.writerows(L)
