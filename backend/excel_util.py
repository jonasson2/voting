import xlsxwriter
from datetime import datetime
from measure_groups import MeasureGroups
from table_util import add_total
from util import disp, isPosInt
from copy import copy
import numpy as np

from table_util import m_subtract, add_totals, find_percentages
from dictionaries import ADJUSTMENT_METHOD_NAMES, \
                         RULE_NAMES, \
                         GENERATING_METHOD_NAMES, \
                         EXCEL_HEADINGS, \
                         STATISTICS_HEADINGS, \
                         SCALING_NAMES, \
                         SEAT_SPECIFICATION_OPTIONS

AMN = {amn["value"]: amn["text"] for amn in ADJUSTMENT_METHOD_NAMES}
DRN = {rn["value"]: rn["text"] for rn in RULE_NAMES}
GMN = {gmn["value"]: gmn["text"] for gmn in GENERATING_METHOD_NAMES}
SCONST = {sso["value"]: sso["text"] for sso in SEAT_SPECIFICATION_OPTIONS["const"]}
SPARTY = {sso["value"]: sso["text"] for sso in SEAT_SPECIFICATION_OPTIONS["party"]}
DEFAULT_FRACTIONAL_DIGITS = 2
DEFAULT_PERCENTAGE_DIGITS = 1


def fixed_seat_threshold_text(system):
    local = system["constituency_threshold"]
    national = system["fixed_seat_national_threshold"]
    if not national and not local:
        return "-"
    if not national:
        return f'{local:g}% local'
    if not local:
        return f'{national:g}% national'
    choice = "or" if system["fixed_seat_threshold_choice"] else "and"
    return f'{national:g}% national {choice} {local:g}% local'


def adjustment_qualification_text(system):
    national = system["adjustment_threshold"]
    fixed = system["adjustment_threshold_seats"]
    if national and fixed:
        choice = "or" if system["adj_threshold_choice"] else "and"
        text = f"{national:g}% {choice} {fixed} fixed seat(s)"
    elif national:
        text = f"{national:g}%"
    elif fixed:
        text = f"{fixed} fixed seat(s)"
    else:
        text = "-"
    if system["require_votes_in_all_constituencies"]:
        text += "; must stand in all constituencies"
    if system["special_rules"] != "none":
        text += "; special rules: " + system["special_rules"].title()
    return text


def result_fractional_digits(display_settings=None):
    value = (display_settings or {}).get(
        "fractional_digits", DEFAULT_FRACTIONAL_DIGITS)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
        raise ValueError("Fractional digits must be an integer between 0 and 10")
    return value


def result_percentage_digits(display_settings=None):
    value = (display_settings or {}).get(
        "percentage_digits", DEFAULT_PERCENTAGE_DIGITS)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
        raise ValueError("Percentage digits must be an integer between 0 and 10")
    return value


def result_number_format(fractional_digits, percentage=False):
    decimals = "." + "0" * fractional_digits if fractional_digits else ""
    return "#,##0" + decimals + ("%" if percentage else "")


def prepare_formats(workbook, display_settings=None):
    fractional_digits = result_fractional_digits(display_settings)
    percentage_digits = result_percentage_digits(display_settings)
    result_format = result_number_format(fractional_digits)
    percentage_format = result_number_format(percentage_digits, True)
    formats = {}
    formats["cell"] = workbook.add_format()
    formats["cell"].set_align('right')
    formats["cell"].set_num_format(result_format)

    formats["votes"] = workbook.add_format()
    formats["votes"].set_align('right')
    formats["votes"].set_num_format('#,##0')

    
    formats["center"] = workbook.add_format()
    formats["center"].set_align('center')

    formats["h_center"] = workbook.add_format()
    formats["h_center"].set_bold()
    formats["h_center"].set_align('center')
    formats["h_center"].set_font_size(11)

    formats["right"] = workbook.add_format()
    formats["right"].set_align('right')

    formats["percentages"] = workbook.add_format()
    formats["percentages"].set_num_format(percentage_format)

    formats["neg-margins"] = workbook.add_format()
    formats["neg-margins"].set_num_format(percentage_format)

    formats["left-pct1"] = workbook.add_format()
    formats["left-pct1"].set_num_format(percentage_format)
    formats["left-pct1"].set_align('left')

    formats["threshold"] = workbook.add_format()
    formats["threshold"].set_num_format(percentage_format)
    formats["threshold"].set_align('center')

    formats["h"] = workbook.add_format()
    formats["h"].set_align('left')
    formats["h"].set_bold()
    formats["h"].set_font_size(11)

    # formats["h_big"] = workbook.add_format()
    # formats["h_big"].set_align('left')
    # formats["h_big"].set_bold()
    # formats["h_big"].set_font_size(14)

    formats["h_right"] = workbook.add_format()
    formats["h_right"].set_align('right')
    formats["h_right"].set_bold()
    formats["h_right"].set_font_size(11)

    formats["time"] = workbook.add_format()
    formats["time"].set_num_format('dd/mm/yy hh:mm')
    formats["time"].set_align('left')

    formats["basic"] = workbook.add_format()
    formats["basic"].set_font_size(11)
    formats["basic"].set_align('left')

    formats["step_h"] = workbook.add_format()
    formats["step_h"].set_bold()
    #formats["step_h"].set_text_wrap()
    formats["step_h"].set_align('center')

    #formats["step"] = workbook.add_format()
    #formats["step"].set_text_wrap()
    #formats["step"].set_align('center')

    formats["inter_h"] = workbook.add_format()
    formats["inter_h"].set_align('left')
    formats["inter_h"].set_bold()
    formats["inter_h"].set_italic()
    formats["inter_h"].set_font_size(11)

    formats["base"] = workbook.add_format()
    formats["base"].set_num_format('#,##0')

    formats["sim"] = workbook.add_format()
    formats["sim"].set_num_format(result_format)

    formats["c"] = workbook.add_format()
    #formats["c"].set_text_wrap()
    formats["c"].set_align('center')

    formats["l"] = workbook.add_format()
    #formats["l"].set_text_wrap()
    formats["l"].set_align('left')
    
    formats["1"] = workbook.add_format()
    formats["1"].set_align('center')
    formats["1"].set_num_format('#,##0.0')
    
    formats["3"] = workbook.add_format()
    formats["3"].set_align('center')
    formats["3"].set_num_format(result_format)

    formats["%"] = workbook.add_format()
    formats["%"].set_align('center')
    formats["%"].set_num_format(percentage_format)
    
    return formats

def write_matrix(worksheet, startrow, startcol,
                 matrix,
                 format,
                 display_zeros = False,
                 totalsformat = None):
    total = totalsformat is not None
    for c in range(len(matrix)):
        ncols = len(matrix[c]) - (1 if total else 0)
        formatc = format[c] if isinstance(format, list) else format
        for p in range(ncols):
            if matrix[c][p] != 0 or display_zeros:
                worksheet.write(startrow+c, startcol+p, matrix[c][p], formatc)
        if total:
            value = round(matrix[c][-1], 8)
            value = int(value) if isPosInt(value) else value
            worksheet.write(startrow+c, startcol+len(matrix[c])-1, value, totalsformat)

def cell_width(
        x, fmt, fractional_digits=DEFAULT_FRACTIONAL_DIGITS,
        percentage_digits=DEFAULT_PERCENTAGE_DIGITS):
    if isinstance(x,str): n = len(x)
    elif fmt == '1':      n = len(f'{x:,.1f}')
    elif fmt == '3':      n = len(f'{x:,.{fractional_digits}f}')
    elif fmt == '%':      n = len(f'{x:,.{percentage_digits}%}')
    elif fmt == 'votes':  n = len(f'{x:,.0f}')
    else:                 n = 10
    return n

def demo_table_to_xlsx(
        worksheet,
        row,
        col,
        fmt,
        demo_table,
        fractional_digits=DEFAULT_FRACTIONAL_DIGITS,
        percentage_digits=DEFAULT_PERCENTAGE_DIGITS,
):
    headers = demo_table["headers"]
    steps = demo_table["steps"]
    row += 1
    if len(steps) == 0:
        worksheet.write(row, col, "There are no steps to show")
        return col+1
    if demo_table["sup_header"]:
        worksheet.write(row, col, demo_table["sup_header"], fmt["h"])
        row += 1
    worksheet.write_row(row, col, headers, fmt["step_h"])
    width = [len(h) for h in headers]
    row += 1
    for i in range(len(steps)):
        for j,(stp,f) in enumerate(zip(steps[i], demo_table["format"])):
            if f=="s": #special
                maxw = max(len(s[j]) for s in steps)
                f = "c" if maxw <= 2 else "l"
            if isinstance(stp, str):
                stp = stp.replace('\n', ',  ')
            elif np.isinf(stp):
                stp = "N/A"
            width[j] = max(width[j], cell_width(
                stp, f, fractional_digits, percentage_digits))
            worksheet.write(row, col + j, stp, fmt[f])
        row += 1
    for j in range(len(headers)):
        worksheet.set_column(col + j, col + j, round(1 + width[j]*0.75))
    col += len(headers) + 1
    return col

def party_names_to_xlsx(workbook, fmt, parties, party_names):
    if not party_names or not any(party_names):
        return
    worksheet = workbook.add_worksheet("Party names")
    worksheet.set_column(0, 0, 15)
    worksheet.set_column(1, 1, max(20, max(len(name) for name in party_names)))
    worksheet.write_row(0, 0, ["Abbreviation", "Name"], fmt["h"])
    for row, (party, name) in enumerate(zip(parties, party_names), start=1):
        worksheet.write_row(row, 0, [party, name], fmt["basic"])


def _draw_election_block(
        worksheet, fmt, row, col, heading, xheaders, yheaders, matrix,
        topleft="", cell_format=None, right_column=None, bottom_row=None):
    cell_format = cell_format or fmt["cell"]
    if heading.endswith("percentages"):
        cell_format = fmt["percentages"]
    worksheet.write(row, col, heading, fmt["h"])
    worksheet.write(row + 1, col, topleft, fmt["basic"])
    worksheet.write_row(row + 1, col + 1, xheaders, fmt["center"])
    worksheet.write_column(row + 2, col, yheaders, fmt["basic"])
    write_matrix(
        worksheet, row + 2, col + 1, matrix,
        format=cell_format, display_zeros=False)
    if right_column:
        header, values, value_format = right_column
        worksheet.write(
            row + 1, col + len(xheaders) + 1, header, fmt["center"])
        worksheet.write_column(
            row + 2, col + len(xheaders) + 1, values, value_format)
    if bottom_row:
        header, values, value_format = bottom_row
        worksheet.write(row + len(matrix) + 2, col, header, fmt["basic"])
        worksheet.write_row(
            row + len(matrix) + 2, col + 1, values, value_format)
    return row + len(matrix) + 3 + bool(bottom_row)


def _election_information(result):
    system = result["system"]
    return [
        ("Date:", datetime.now().strftime('%Y-%m-%d %H:%M')),
        ("Vote table:", result["vote_table_name"]),
        ("Electoral system:", system["name"]),
        ("Rule for allocating fixed seats:", DRN[system["primary_divider"]]),
        ("Fixed-seat thresholds:", fixed_seat_threshold_text(system)),
        ("Rule for apportioning adjustment seats:",
         DRN[system["adj_determine_divider"]]),
        ("Threshold for adjustment seats:",
         adjustment_qualification_text(system)),
        ("Rule for allocating adjustment seats:",
         DRN[system["adj_alloc_divider"]]),
        ("Method for allocating adjustment seats:",
         AMN[system["adjustment_method"]]),
    ]


def _vote_percentages(vote_matrix):
    total = vote_matrix[-1][-1]
    parties = [value / total if total else 0 for value in vote_matrix[-1]]
    constituencies = [row[-1] / total if total else 0 for row in vote_matrix]
    return parties, constituencies


def _write_election_sheet(
        workbook, fmt, result, fractional_digits, percentage_digits):
    system = result["system"]
    worksheet = workbook.add_worksheet(system["name"][:31])
    worksheet.set_column(0, 0, 31)
    parties = system["parties"] + ["Total"]
    row = 0
    for title, item in _election_information(result):
        worksheet.write(row, 0, title, fmt["h"])
        worksheet.write(row, 1, item, fmt["basic"])
        row += 1
    row += 1

    results = result["results"]
    yheaders = results["row_names"]
    row = _draw_election_block(
        worksheet, fmt, row, 0, "Required number of seats",
        ["Const.", "Adj.", "Total"], yheaders, results["seats"],
        cell_format=fmt["base"])
    vote_matrix = results["votes"]
    party_percentages, constituency_percentages = _vote_percentages(vote_matrix)
    row = _draw_election_block(
        worksheet, fmt, row, 0, "Votes", parties, yheaders, vote_matrix,
        cell_format=fmt["base"],
        right_column=(
            "Vote percentage", constituency_percentages, fmt["percentages"]),
        bottom_row=(
            "Vote percentage", party_percentages + [1], fmt["percentages"]))
    for heading, key in (
            ("Fixed seats", "fix"),
            ("Adjustment seats", "adj")):
        row = _draw_election_block(
            worksheet, fmt, row, 0, heading, parties, yheaders,
            results[key], cell_format=fmt["base"])
    row = _draw_election_block(
        worksheet, fmt, row, 0, "Total seats", parties, yheaders,
        results["all"], cell_format=fmt["base"],
        right_column=(
            "Average votes/seat",
            [votes[-1] / seats[-1] if seats[-1] else None
             for votes, seats in zip(vote_matrix, results["all"])],
            fmt["cell"]))
    worksheet.write(row, 0, "Entropy score:", fmt["h"])
    score = result["entropy_score"]
    worksheet.write(
        row, 1, "–" if score is None else score, fmt["percentages"])
    row += 1

    column = len(parties) + 2
    worksheet.set_column(1, column - 1, 10)
    worksheet.write(
        0, column, "Allocation of adjustment seats step-by-step", fmt["h"])
    for demo_table in result["demo_tables"]:
        column = demo_table_to_xlsx(
            worksheet, 1, column, fmt, demo_table,
            fractional_digits, percentage_digits)


def elections_to_xlsx(elections, filename, party_names=None, display_settings=None):
    """Write one vote table evaluated under multiple electoral systems."""
    workbook = xlsxwriter.Workbook(filename)
    fmt = prepare_formats(workbook, display_settings)
    fractional_digits = result_fractional_digits(display_settings)
    percentage_digits = result_percentage_digits(display_settings)
    entropy_cache = {}
    for election in elections:
        _write_election_sheet(
            workbook, fmt, election.get_result_excel(entropy_cache),
            fractional_digits, percentage_digits)
    party_names_to_xlsx(
        workbook, fmt, elections[0].system["parties"], party_names)
    workbook.close()

def simulation_to_xlsx(results, filename, display_settings=None,
                       include_histogram_sheets=False):
    """Write detailed information about a simulation to an xlsx file."""
    from simulation_excel import SimulationWorkbook

    SimulationWorkbook(
        results,
        filename,
        display_settings,
        include_histogram_sheets,
    ).write()


def votes_to_xlsx(votes, party_vote_info, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    worksheet.set_column(0, 0, 15)
    fmt = prepare_formats(workbook)
    write_matrix(worksheet, 0, 0, votes, fmt["votes"])
    if party_vote_info:
        write_matrix(worksheet, len(votes) + 1, 0, party_vote_info, fmt["votes"])
    workbook.close()
