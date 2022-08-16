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
                         SCALING_NAMES

AMN = {amn["value"]: amn["text"] for amn in ADJUSTMENT_METHOD_NAMES}
DRN = {rn["value"]: rn["text"] for rn in RULE_NAMES}
GMN = {gmn["value"]: gmn["text"] for gmn in GENERATING_METHOD_NAMES}

def prepare_formats(workbook):
    formats = {}
    formats["cell"] = workbook.add_format()
    formats["cell"].set_align('right')
    formats["cell"].set_num_format('#,##0.000')

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
    formats["percentages"].set_num_format('0.0%')

    formats["left-pct1"] = workbook.add_format()
    formats["left-pct1"].set_num_format('0.0%')
    formats["left-pct1"].set_align('left')

    formats["threshold"] = workbook.add_format()
    formats["threshold"].set_num_format('0.0%')
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
    formats["sim"].set_num_format('#,##0.000')

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
    formats["3"].set_num_format('#,##0.000')

    formats["%"] = workbook.add_format()
    formats["%"].set_align('center')
    formats["%"].set_num_format('#,##0.000%')
    
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

def cell_width(x, fmt):
    if isinstance(x,str): n = len(x)
    elif fmt == '1':      n = len(f'{x:,.1f}')
    elif fmt == '3':      n = len(f'{x:,.3f}')
    elif fmt == '%':      n = len(f'{x:,.3%}')
    elif fmt == 'votes':  n = len(f'{x:,.0f}')
    else:                 n = 10
    return n

def demo_table_to_xlsx(
        worksheet,
        row,
        col,
        fmt,
        demo_table
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
            width[j] = max(width[j], cell_width(stp, f))
            worksheet.write(row, col + j, stp, fmt[f])
        row += 1
    for j in range(len(headers)):
        worksheet.set_column(col + j, col + j, round(1 + width[j]*0.75))
    col += len(headers) + 1
    return col

def elections_to_xlsx(elections, filename):
    """Write detailed information about an election with a single vote table
    but multiple electoral systems, to an xlsx file.
    """
    workbook = xlsxwriter.Workbook(filename)
    fmt = prepare_formats(workbook)

    def draw_block(worksheet, row, col,
        heading, xheaders, yheaders,
        matrix,
        topleft="",
        cformat=fmt["cell"]
    ):
        if heading.endswith("percentages"):
            cformat = fmt["percentages"]
        worksheet.write(row, col, heading, fmt["h"])
        worksheet.write(row+1, col, topleft, fmt["basic"])
        worksheet.write_row(row+1, col+1, xheaders, fmt["center"])
        worksheet.write_column(row+2, col, yheaders, fmt["basic"])
        write_matrix(worksheet, row+2, col+1, matrix,
                     format = cformat,
                     display_zeros = False)
        return row + len(matrix) + 3

    for election in elections:
        result = election.get_result_excel()
        system = result["system"]
        sheet_name = system["name"]
        worksheet = workbook.add_worksheet(sheet_name[:31])
        worksheet.set_column(0, 0, 31)
        parties = system["parties"] + ["Total"]
        #xtd_votes = add_totals(election.m_votes)
        #xtd_fixed_seats = add_totals(election.m_fixed_seats)
        #xtd_total_seats = add_totals(election.results)
        #xtd_adj_seats = m_subtract(xtd_total_seats, xtd_fixed_seats)
        # xtd_final_votes = add_totals([election.v_votes_eliminated])[0]
        # xtd_final_shares = find_percentages([xtd_final_votes])[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        info = [
            ["Date:",
             now,
             "basic"
             ],
            ["Vote table:",
             result["vote_table_name"],
             "basic"
             ],
            ["Electoral system:",
             system["name"],
             "basic"],
            ["Rule for allocating fixed seats:",
             DRN[system["primary_divider"]],
             "basic"
             ],
            ["Threshold for fixed seats:",
             system["constituency_threshold"]/100,
             "left-pct1"
             ],
            ["Rule for apportioning adjustment seats:",
             DRN[system["adj_determine_divider"]],
             "basic"
             ],
            ["Threshold for adjustment seats:",
             str(system["adjustment_threshold"]) + "% " +
                 ("or " if system["adj_threshold_choice"] else "and ") +
                 str(system["adjustment_threshold_seats"]) + " const. seat(s)",
             "basic"
            ],
            ["Rule for allocating adjustment seats:",
             DRN[system["adj_alloc_divider"]],
             "basic"
             ],
            ["Method for allocating adjustment seats:",
             AMN[system["adjustment_method"]],
             "basic"
             ]
        ]
        row = 0
        col = 0
        #Basic info
        for group in info:
            (title,item,format) = group
            worksheet.write(row, col, title, fmt["h"])
            worksheet.write(row, col+1, item, fmt[format])
            row += 1
        row += 1

        yheaders = result["results"]["row_names"]
        row = draw_block(worksheet, row=row, col=col,
            heading = "Required number of seats",
            xheaders = ["Const.", "Adj.", "Total"],
            yheaders = yheaders,
            matrix = result["results"]["seats"],
            cformat=fmt["base"]
        )

        vote_yheaders = copy(yheaders)
        if vote_yheaders[-1] == 'Grand total':
            vote_yheaders.pop()
        row = draw_block(
            worksheet,
            row=row,
            col=col,
            heading="Votes",
            xheaders=parties,
            yheaders = vote_yheaders,
            matrix = result["results"]["votes"],
            cformat=fmt["base"]
        )

        row = draw_block(worksheet, row=row, col=col,
            heading = "Fixed seats", xheaders=parties, yheaders=yheaders,
            matrix = result["results"]["fix"], cformat=fmt["base"]
        )

        row = draw_block(worksheet, row=row, col=col,
            heading="Adjustment seats", xheaders=parties, yheaders=yheaders,
            matrix = result["results"]["adj"], cformat=fmt["base"]
        )

        row = draw_block(worksheet, row=row, col=col,
            heading="Total seats", xheaders=parties, yheaders=yheaders,
            matrix = result["results"]["all"], cformat=fmt["base"]
        )

        worksheet.write(row, col, 'Entropy:', fmt["h"])
        worksheet.write(row, col+1, result["entropy"], fmt["cell"])

        row = 0
        col = len(parties) + 1
        worksheet.set_column(1, col-1, 10)

        worksheet.write(row, col,
            "Allocation of adjustment seats step-by-step",
            fmt["h"]
        )
        for demo_table in result["demo_tables"]:
           col = demo_table_to_xlsx(worksheet, row+1, col, fmt, demo_table)

    workbook.close()

def simulation_to_xlsx(results, filename, parallel):

    """Write detailed information about a simulation to an xlsx file."""
    workbook = xlsxwriter.Workbook(filename)
    fmt = prepare_formats(workbook)

    def draw_sim_block(worksheet, row, col, heading, data, abbreviation, setTotal="hide"):
        cformat = fmt['sim'] if abbreviation in {'avg', 'std'} else fmt['base']
        if heading.endswith("percentages"):
            cformat = fmt["percentages"]
        elif heading.startswith("Reference seat"):
            cformat = fmt["sim"]
            totalsformat = fmt["base"]
        elif heading == "Votes":
            cformat = fmt["base"]
        if setTotal=="hide":
            data = [r[:-1] for r in data]
            totalsformat = None
        else:
            totalsformat = fmt["base"] if setTotal == "integer" else cformat
        write_matrix(worksheet, row, col, data,
                     format = cformat,
                     display_zeros = True,
                     totalsformat = totalsformat)

    gen_method = GMN[results["sim_settings"]["gen_method"]]
    sim_settings = [
        {"label": "Number of simulations run",
         "data": results["iteration"]},
        {"label": "Generating method",
         "data": results["sim_settings"]["gen_method"]},
        {"label": "Coefficient of variation for constituencies",
         "data": results["sim_settings"]["const_cov"]},
        {"label": "Coefficient of variation for party votes",
         "data": results["sim_settings"]["party_vote_cov"]},
        {"label": "Thresholds used",
         "data": "yes" if results["sim_settings"]["use_thresholds"] else "no"},
        {"label": "Apply randomness to",
         "data": results["sim_settings"]["selected_rand_constit"]},
        {"label": "Scaling of votes for reference seat shares",
         "data": SCALING_NAMES[results["sim_settings"]["scaling"]]
        }
    ]

    # COMMON SETTINGS
    worksheet = workbook.add_worksheet("Common settings")
    c1 = 0
    c2 = c1 + 1
    row = 0
    worksheet.set_column(c1, c1, 35)
    worksheet.set_column(c2, c2, 35)
    worksheet.write(row, c1, "Date:", fmt["h"])
    worksheet.write(row, c2, datetime.now(), fmt["time"])
    total_votes = sum(sum(row) for row in results["vote_table"]["votes"])
    total_party_votes = results["vote_table"]["party_vote_info"]["total"]
    fixed_seats = sum(
        c["num_fixed_seats"] for c in results["vote_table"]["constituencies"])
    adj_seats = sum(
        c["num_adj_seats"] for c in results["vote_table"]["constituencies"])
    row += 2
    worksheet.write(row, c1, "Source votes and seats", fmt["h"])
    row += 1
    worksheet.write(row, c1, "Vote table", fmt["basic"])
    worksheet.write(row, c2, results["vote_table"]["name"], fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Number of constituencies", fmt["basic"])
    worksheet.write(row, c2, len(results["vote_table"]["constituencies"]), fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Number of parties", fmt["basic"])
    worksheet.write(row, c2, len(results["vote_table"]["parties"]), fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Total number of const. seats", fmt["basic"])
    worksheet.write(row, c2, fixed_seats, fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Total number of adj. seats", fmt["basic"])
    worksheet.write(row, c2, adj_seats, fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Total number of const. votes", fmt["basic"])
    worksheet.write(row, c2, total_votes, fmt["basic"])
    row += 1
    worksheet.write(row, c1, "Total number of national party votes", fmt["basic"])
    worksheet.write(row, c2, total_party_votes, fmt["basic"])

    row += 2
    worksheet.write(row, c1, "Simulation settings", fmt["h"])
    for setting in sim_settings:
        row += 1
        worksheet.write(row, c1, setting["label"], fmt["basic"])
        worksheet.write(row, c2, setting["data"], fmt["basic"])
    
    categories = [
        {"abbr": "base", "heading": "Values based on source votes"},
        {"abbr": "avg",  "heading": "Avg. simulated values"},
        {"abbr": "min",  "heading": "Minimum values"},
        {"abbr": "max",  "heading": "Maximum values"},
        {"abbr": "std",  "heading": "Standard deviations"}
    ]
    tables = [
        {"abbr": "v",  "heading": "Votes"             },
        {"abbr": "vp", "heading": "Vote percentages"},
        {"abbr": "rss", "heading": "Reference seat shares"},
        {"abbr": "cs", "heading": "Fixed seats"},
        {"abbr": "as", "heading": "Adjustment seats"},
        {"abbr": "ts", "heading": "Total seats"},
        {"abbr": "tsp", "heading": "Total seat percentages"},
    ]
    base_const_names = [c["name"] for c in results["vote_table"]["constituencies"]]
    base_const_names.append("Total")
    if results['vote_table']['party_vote_info']['specified']:
        base_const_names.append(results['vote_table']['party_vote_info']['name'])
        base_const_names.append('Grand total')

    #Measures
    party_votes_specified = results["vote_table"]["party_vote_info"]["specified"]
    data = results["data"]
    systems = results["systems"]
    groups = MeasureGroups(systems, party_votes_specified)
    edata = {}
    edata["stats"] = EXCEL_HEADINGS.keys()
    edata["stat_headings"] = EXCEL_HEADINGS

    for (id, group) in groups.items():
        edata[id] = []
        for (measure, _) in group["rows"].items():
            row = {}
            for stat in edata["stats"]:
                row[stat] = []
                for s in range(len(systems)):
                    row[stat].append(data[s]["measures"][measure][stat])
            edata[id].append(row)

    # QUALITY MEASURES
    worksheet = workbook.add_worksheet("Quality measures")
    worksheet.freeze_panes(4,2)
    toprow = 0
    c = 0
    worksheet.write(toprow,c,"QUALITY MEASURES",fmt["h"])
    toprow += 1
    worksheet.write(toprow,c,"Vote table:",fmt["h"])
    worksheet.write(toprow, c+1, results["vote_table"]["name"], fmt["basic"])
    toprow += 1
    worksheet.set_column(c,c,20)
    c += 1
    worksheet.set_column(c,c,25)
    worksheet.write(toprow+1,c,"Tested systems: ",fmt["h_right"])
    c += 1

    for stat in edata["stats"]:
        worksheet.write(toprow,c,edata["stat_headings"][stat],fmt["h"])
        worksheet.set_column(c,c+len(results["systems"])-1,11)
        for system in results["systems"]:
            worksheet.write(toprow+1,c,system["name"],fmt["h_center"])
            c += 1
        worksheet.set_column(c,c,3)
        c += 1

    c = 0
    toprow += 2

    for (id, group) in groups.items():
        worksheet.write(toprow,c,group["title"],fmt["h"])
        toprow += 1
        worksheet.write_column(toprow,c,
                               [val[0] for (_, val) in group["rows"].items()])
        worksheet.write_column(toprow,c+1,
                               [val[1] for (_, val) in group["rows"].items()])
        for stat in edata["stats"]:
            if stat in ["min","max"] and id in ["seatSpec","expected","cmpSys"]:
                write_matrix(worksheet, toprow, c+2,
                             [row[stat] for row in edata[id]],
                             format = fmt["base"],
                             display_zeros = True)
            else:
                write_matrix(worksheet,toprow,c+2,
                             [row[stat] for row in edata[id]],
                             format = fmt["cell"],
                             display_zeros = True)
            c += len(results["systems"]) + 1
        nrows = len(group["rows"])
        toprow += nrows + 1 if nrows > 0 else 0
        c = 0

    # SYSTEM SHEETS    
    for r in range(len(results["systems"])):
        sheet_name  = results["systems"][r]["name"]
        worksheet   = workbook.add_worksheet(sheet_name[:31])
        worksheet.freeze_panes(10,2)
        parties = results["systems"][r]["parties"] + ["Total"]
        xtd_votes = add_totals(results["vote_table"]["votes"])
        party_votes_specified = results["vote_table"]["party_vote_info"]["specified"]
        if party_votes_specified:
            xtd_votes.append(add_total(results["vote_table"]["party_vote_info"]["votes"]))
        else:
            xtd_votes.append(xtd_votes[-1])
        xtd_percentages = find_percentages(xtd_votes)
        data_matrix = {
            "base": {
                "v" : xtd_votes,
                "vp": xtd_percentages,
                "cs": results["base_allocations"][r]["fixed_seats"],
                "as": results["base_allocations"][r]["adj_seats"],
                "ts": results["base_allocations"][r]["total_seats"],
                "tsp": results["base_allocations"][r]["total_seat_percentages"],
                "rss": results["base_allocations"][r]["ref_seat_shares"],
            }
        }
        seat_measures = results["data"][r]["seat_measures"]
        for stat in STATISTICS_HEADINGS.keys():
            data_matrix[stat] = {
                "v" : results["vote_data"][r]["sim_votes"][stat],
                "vp": results["vote_data"][r]["sim_vote_percentages"][stat],
                "cs": seat_measures["fixed_seats"][stat],
                "as": seat_measures["adj_seats"  ][stat],
                "ts": seat_measures["total_seats"][stat],
                "tsp": seat_measures["total_seat_percentages"][stat],
                "rss": seat_measures["ref_seat_shares"][stat],
            }
        alloc_info = [{
            "left_span": 2, "center_span": 2, "right_span": 1, "info": [
                {"label": "Allocation of fixed seats:",
                    "rule": DRN[results["systems"][r]["primary_divider"]],
                    "threshold": (
                        str(results["systems"][r]["constituency_threshold"]) + "%")},
                {"label": "Apportionment of adjustment seats to parties:",
                    "rule": DRN[results["systems"][r]["adj_determine_divider"]],
                    "threshold": (
                        str(results["systems"][r]["adjustment_threshold"]) + "% " +
                        ("or " if results["systems"][r]["adj_threshold_choice"] else "and ") +
                        str(results["systems"][r]["adjustment_threshold_seats"]) +
                        " const. seat(s)")},
                {"label": "Allocation of adjustment seats to lists:",
                    "rule": DRN[results["systems"][r]["adj_alloc_divider"]],
                    "threshold": None}
            ]
        }, {
            "left_span": 2, "center_span": 2, "right_span": 0, "info": [
                {"label": "Allocation method for adjustment seats:",
                    "rule": AMN[results["systems"][r]["adjustment_method"]]}
            ]
        }]

        toprow = 0
        c1 = 0
        c2 = c1 + 1
        worksheet.set_row_pixels(0,25)
        worksheet.set_column(c1,c1,25)
        worksheet.set_column(c2,c2,20)
        worksheet.write(toprow, c1, "Electoral system:", fmt["h"])
        worksheet.write(toprow, c2, results["systems"][r]["name"], fmt["basic"])
        toprow += 1
        worksheet.write(toprow, c2, results["vote_table"]["name"], fmt["basic"])
        toprow += 1
        worksheet.write(toprow, c2+1, "Rule", fmt["h"])
        worksheet.write(toprow, c2+3, "Threshold", fmt["h"])

        toprow += 1
        for group in alloc_info:
            c2 = c1 + group["left_span"]
            c3 = c2 + group["center_span"]
            for info in group["info"]:
                worksheet.write(toprow, c1, info["label"], fmt["h"])
                worksheet.write(toprow, c2, info["rule"], fmt["basic"])
                if group["right_span"] > 0:
                    worksheet.write(toprow, c3, info["threshold"],
                                    fmt["basic"])
                toprow += 1

        toprow += 1
        worksheet.set_row_pixels(toprow, 25)
        worksheet.write(toprow, c1, "Simulation results", fmt["h"])
        
        col = 2
        for table in tables:
            is_percentages_table = (
                table["heading"].endswith("percentages") and
                not table["heading"].startswith("Reference"))
            worksheet.write(toprow, col, table["heading"], fmt["h"])
            worksheet.write_row(
                toprow+1,
                col,
                parties[:-1] if is_percentages_table else parties,
                fmt["h_center"])
            col += len(parties[:-1] if is_percentages_table else parties)+1
            worksheet.set_column(col-1,col-1,3)

        toprow += 2

        worksheet.set_column(2,len(parties)+1,10)
        
        #Election tables
        for category in categories:
            worksheet.write(toprow, 0, category["heading"], fmt["h"])
            worksheet.write_column(toprow, 1, base_const_names, fmt["basic"])
            col = 2
            for table in tables:
                is_refseatshare_table = table["heading"].startswith("Reference")
                is_percentages_table = \
                    table["heading"].endswith("percentages") and not is_refseatshare_table
                setTotal = (
                    "hide" if is_percentages_table else
                    "integer" if is_refseatshare_table else
                    "show")
                draw_sim_block(worksheet, row=toprow, col=col,
                    heading = table["heading"],
                    data = data_matrix[category["abbr"]][table["abbr"]],
                    abbreviation = category["abbr"],
                    setTotal = setTotal
                )
                col += len(parties[:-1] if is_percentages_table else parties)+1
            toprow += len(base_const_names)+1
    '''
    #   ALLOCATION SUMMARY
    nsys = len(results["systems"])
    summary_tables = [
        {"abbr": "vp", "heading": "Vote percentages"},
        {"abbr": "rss", "heading": "Reference seat shares"},
        {"abbr": "ts", "heading": "Total seats"},
        {"abbr": "ra", "heading": "Reference allocations"},
        {"abbr": "dis", "heading": "Disparity (excess if positive/deficiency if negative)"},
    ]
    data_matrix = {
        "base": {
            "vp": [xtd_percentages[-1]] * nsys,
            "rss": [results["base_allocations"][r]["ref_seat_shares"][-1] for r in range(nsys)],
            "ts": results["base_allocations"][r]["total_seats"],
            "ra": results["base_allocations"][r]["ref_allocations"],
            "dis": results["base_allocations"][r]["ref_allocations"],
        }
    }
    seat_measures = results["data"][0]["seat_measures"]
    for stat in STATISTICS_HEADINGS.keys():
        data_matrix[stat] = {
            "vp": [results["vote_data"][r]["sim_vote_percentages"][stat][-1] for r in range(nsys)],
            "rss": seat_measures["ref_seat_shares"][stat],
            "ts": seat_measures["total_seats"][stat],
            "ra": seat_measures["ref_seat_shares"][stat],
        }

    parties = results["systems"][r]["parties"] + ["Total"]
    party_votes_specified = results["vote_table"]["party_vote_info"]["specified"]

    system_names = [sys["name"] for sys in results["systems"]]

    # WRITING ALLOCATION SUMMARY
    worksheet   = workbook.add_worksheet("Allocation summary")
    worksheet.freeze_panes(4,2)
    toprow = 0
    c = 0
    worksheet.write(toprow,c,"QUALITY MEASURES",fmt["h"])
    toprow += 1
    worksheet.write(toprow,c,"Vote table:",fmt["h"])
    worksheet.write(toprow, c+1, results["vote_table"]["name"], fmt["basic"])
    toprow += 1
    worksheet.set_column(c,c,20)
    c += 1
    worksheet.set_column(c,c,25)    
    worksheet.write(toprow+1,c,"Electoral system",fmt["h_left"])
    toprow += 1
    #Election tables
    for category in categories:
        worksheet.write(toprow, 0, category["heading"], fmt["h"])
        worksheet.write_column(toprow, 1, system_names, fmt["basic"])
        col = 2
        for table in summary_tables:
            is_refseatshare_table = table["heading"].startswith("Reference")
            is_percentages_table = \
                table["heading"].endswith("percentages") and not is_refseatshare_table
            setTotal = (
                "hide" if is_percentages_table else
                "integer" if is_refseatshare_table else
                "show")
            draw_sim_block(worksheet, row=toprow, col=col,
                heading = table["heading"],
                data = data_matrix[category["abbr"]][table["abbr"]],
                abbreviation = category["abbr"],
                setTotal = setTotal
            )
            col += len(parties[:-1] if is_percentages_table else parties)+1
        toprow += len(base_const_names)+1
    '''
    workbook.close()

def votes_to_xlsx(votes, party_vote_info, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    worksheet.set_column(0, 0, 15)
    fmt = prepare_formats(workbook)
    write_matrix(worksheet, 0, 0, votes, fmt["votes"])
    if party_vote_info:
        write_matrix(worksheet, len(votes) + 1, 0, party_vote_info, fmt["votes"])
    workbook.close()
