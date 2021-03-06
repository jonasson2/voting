import xlsxwriter
from datetime import datetime
from measure_groups import MeasureGroups
from util import disp

from table_util import m_subtract, add_totals, find_xtd_shares
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

    formats["share"] = workbook.add_format()
    formats["share"].set_num_format('0.0%')

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

    formats["h_big"] = workbook.add_format()
    formats["h_big"].set_align('left')
    formats["h_big"].set_bold()
    formats["h_big"].set_font_size(14)

    formats["h_right"] = workbook.add_format()
    formats["h_right"].set_align('right')
    formats["h_right"].set_bold()
    formats["h_right"].set_font_size(11)

    formats["time"] = workbook.add_format()
    formats["time"].set_num_format('dd/mm/yy hh:mm')
    formats["time"].set_align('left')

    formats["basic"] = workbook.add_format()
    formats["basic"].set_align('left')

    formats["basic_h"] = workbook.add_format()
    formats["basic_h"].set_align('left')
    formats["basic_h"].set_bold()
    formats["basic_h"].set_font_size(11)

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

def write_matrix(worksheet, startrow, startcol, matrix, cformat, display_zeroes=False,
                 totalsformat = None, zeroesformat = None):
    total = totalsformat is not None
    for c in range(len(matrix)):
        nrows = len(matrix[c]) - (1 if total else 0)
        formatc = cformat[c] if isinstance(cformat, list) else cformat
        for p in range(nrows):
            if matrix[c][p] != 0 or display_zeroes:
                try:
                    worksheet.write(startrow+c, startcol+p, matrix[c][p], formatc)
                except TypeError:
                    if matrix[c][p] == 0 and zeroesformat is not None:
                        worksheet.write(startrow+c, startcol+p, matrix[c][p], zeroesformat)
                    else:
                        worksheet.write(startrow+c, startcol+p, matrix[c][p], formatc)
        if total:
            worksheet.write(startrow+c, startcol+len(matrix[c])-1, matrix[c][-1],
                    totalsformat)

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
        topleft="Constituency",
        cformat=fmt["cell"]
    ):
        if heading.endswith("shares"):
            cformat = fmt["share"]
        worksheet.write(row, col, heading, fmt["h"])
        worksheet.write(row+1, col, topleft, fmt["basic"])
        worksheet.write_row(row+1, col+1, xheaders, fmt["center"])
        worksheet.write_column(row+2, col, yheaders, fmt["basic"])
        write_matrix(worksheet, row+2, col+1, matrix, cformat)
        return row + len(matrix) + 3

    for r in range(len(elections)):
        election = elections[r]
        system = election.system
        sheet_name = f'{r+1}-{system["name"]}'
        worksheet = workbook.add_worksheet(sheet_name[:31])
        worksheet.set_column(0, 0, 31)
        const_names = [
            const["name"] for const in system["constituencies"]
        ] + ["Total"]
        parties = system["parties"] + ["Total"]
        xtd_votes = add_totals(election.m_votes)
        xtd_shares = find_xtd_shares(xtd_votes)
        xtd_const_seats = add_totals(election.m_const_seats)
        xtd_total_seats = add_totals(election.results)
        xtd_adj_seats = m_subtract(xtd_total_seats, xtd_const_seats)
        xtd_seat_shares = find_xtd_shares(xtd_total_seats)
        threshold = 0.01*election.system["adjustment_threshold"]
        # xtd_final_votes = add_totals([election.v_votes_eliminated])[0]
        # xtd_final_shares = find_xtd_shares([xtd_final_votes])[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        info = [
            ["Date:",
             now,
             "basic"
             ],
            ["Vote table:",
             election.name,
             "basic"
             ],
            ["Electoral system:",
             system["name"],
             "basic"],
            ["Rule for allocating constituency seats:",
             DRN[system["primary_divider"]],
             "basic"
             ],
            ["Threshold for constituency seats:",
             system["constituency_threshold"]/100,
             "left-pct1"
             ],
            ["Rule for apportioning adjustment seats:",
             DRN[system["adj_determine_divider"]],
             "basic"
             ],
            ["Threshold for adjustment seats:",
             system["adjustment_threshold"]/100,
             "left-pct1"
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
            (title,item,f) = group
            worksheet.write(row, col, title, fmt["basic_h"])
            worksheet.write(row, col+1, item, fmt[f])
            row += 1
        row += 1

        row = draw_block(worksheet, row=row, col=col,
            heading="Required number of seats",
            xheaders=["Const.", "Adj.", "Total"],
            yheaders=const_names,
            matrix=add_totals([
                [const["num_const_seats"],const["num_adj_seats"]]
                for const in system["constituencies"]
            ]),
            cformat=fmt["base"]
        )

        row = draw_block(worksheet, row=row, col=col,
            heading="Votes", xheaders=parties, yheaders=const_names,
            matrix=xtd_votes, cformat=fmt["base"]
        )

        # row = draw_block(worksheet, row=row, col=col,
        #     heading="Vote percentages", xheaders=parties, yheaders=const_names,
        #     matrix=xtd_shares
        # )

        row = draw_block(worksheet, row=row, col=col,
            heading="Constituency seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_const_seats, cformat=fmt["base"]
        )

        # row_headers = ['Total votes', 'Vote shares', 'Threshold',
        #                'Votes above threshold',
        #                'Vote shares above threshold', 'Constituency seats']
        # matrix = [xtd_votes[-1],   xtd_shares[-1],   [threshold],
        #           xtd_final_votes, xtd_final_shares, xtd_const_seats[-1]]
        # formats = [fmt["base"], fmt["share"], fmt["share"],
        #            fmt["base"], fmt["share"], fmt["base"]]
        # row = draw_block(worksheet, row=row, col=col,
        #     heading="Adjustment seat apportionment", topleft="Party",
        #     xheaders=parties, yheaders=row_headers,
        #     matrix=matrix, cformat=formats
        # )

        row = draw_block(worksheet, row=row, col=col,
            heading="Adjustment seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_adj_seats, cformat=fmt["base"]
        )

        row = draw_block(worksheet, row=row, col=col,
            heading="Total seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_total_seats, cformat=fmt["base"]
        )

        # row = draw_block(worksheet, row=row, col=col,
        #     heading="Seat shares", xheaders=parties, yheaders=const_names,
        #     matrix=xtd_seat_shares
        # )

        worksheet.write(row, col, 'Entropy:', fmt["h"])
        worksheet.write(row, col+1, election.entropy(), fmt["cell"])

        row = 0
        col = len(parties) + 1
        worksheet.set_column(1, col-1, 10)

        worksheet.write(row, col,
            "Allocation of adjustment seats step-by-step",
            fmt["h"]
        )
        for demo_table in election.demo_tables:
           col = demo_table_to_xlsx(worksheet, row+1, col, fmt, demo_table)

        #suph = [] if suph is None else suph

    workbook.close()

def simulation_to_xlsx(results, filename, parallel):

    """Write detailed information about a simulation to an xlsx file."""
    workbook = xlsxwriter.Workbook(filename)
    fmt = prepare_formats(workbook)

    def draw_block(worksheet, row, col,
        heading,
        matrix,
        cformat=fmt["cell"],
        hideTotals=False
    ):
        totalsformat = None
        if hideTotals:
            matrix = [r[:-1] for r in matrix]
        if heading.endswith("shares"):
            cformat = fmt["share"]
        ideal_or_reference = (heading.lower().startswith("ideal") or
                              heading.lower().startswith("reference"))
        if ideal_or_reference:
            cformat = fmt["cell"]
            totalsformat = fmt["base"]
        if heading == "Votes":
            cformat = fmt["base"]
        write_matrix(worksheet, row, col, matrix, cformat, False, totalsformat)

    gen_method = GMN[results["sim_settings"]["gen_method"]]
    sim_settings = [
        {"label": "Number of simulations run",
         "data": results["iteration"]},
        {"label": "Generating method",
         "data": results["sim_settings"]["gen_method"]},
        {"label": "Coefficient of variation",
         "data": results["sim_settings"]["distribution_parameter"]},
        {"label": "Apply randomness to",
         "data": results["sim_settings"]["selected_rand_constit"]},
        {"label": "Scaling of votes for reference seat shares",
         "data": SCALING_NAMES[results["sim_settings"]["scaling"]]
        }
    ]

    worksheet = workbook.add_worksheet("Common settings")
    c1 = 0
    c2 = c1 + 1
    row = 0
    worksheet.set_column(c1, c1, 30)
    worksheet.set_column(c2, c2, 35)
    worksheet.write(row, c1, "Date", fmt["basic_h"])
    worksheet.write(row, c2, datetime.now(), fmt["time"])
    row += 2
    worksheet.write(row, c1, "Source votes and seats", fmt["basic_h"])
    row += 2
    worksheet.write(row, c1, "Simulation settings", fmt["basic_h"])
    for setting in sim_settings:
        row += 1
        worksheet.write(row, c1, setting["label"], fmt["basic"])
        worksheet.write(row, c2, setting["data"], fmt["basic"])
    
    categories = [
        {"abbr": "base", "cell_format": fmt["base"],
         "heading": "Values based on source votes"},
        {"abbr": "avg",  "cell_format": fmt["sim"],
         "heading": "Avg. simulated values"},
        {"abbr": "min",  "cell_format": fmt["base"],
         "heading": "Minimum values"},
        {"abbr": "max",  "cell_format": fmt["base"],
         "heading": "Maximum values"},
        {"abbr": "std",  "cell_format": fmt["sim"],
         "heading": "Standard deviations"}
        # {"abbr": "skw",  "cell_format": fmt["sim"],
        #  "heading": "Skewness"},
        # {"abbr": "kur",  "cell_format": fmt["sim"],
        #  "heading": "Kurtosis"}
    ]
    tables = [
        {"abbr": "v",  "heading": "Votes"             },
        {"abbr": "vs", "heading": "Vote shares"       },
        {"abbr": "id", "heading": "Reference seat shares" },
        {"abbr": "cs", "heading": "Constituency seats"},
        {"abbr": "as", "heading": "Adjustment seats"  },
        {"abbr": "ts", "heading": "Total seats"       },
        {"abbr": "ss", "heading": "Seat shares"       },
    ]
    base_const_names = [c["name"] for c in results["vote_table"]["constituencies"]]
    base_const_names.append("Total")

    #Measures
    data = results["data"]
    systems = results["systems"]
    groups = MeasureGroups(systems)
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

    worksheet = workbook.add_worksheet("Quality measures")
    worksheet.freeze_panes(2,2)
    toprow = 0
    c = 0
    worksheet.write(toprow,c,"QUALITY MEASURES",fmt["h_big"])
    worksheet.set_column(c,c,16)
    c += 1
    worksheet.set_column(c,c,25)
    worksheet.write(toprow+1,c,"Tested systems: ",fmt["h_right"])
    c += 1

    for stat in edata["stats"]:
        worksheet.write(toprow,c,edata["stat_headings"][stat],fmt["basic_h"])
        worksheet.set_column(c,c+len(results["systems"])-1,11)
        for system in results["systems"]:
            worksheet.write(toprow+1,c,system["name"],fmt["h_center"])
            c += 1
        worksheet.set_column(c,c,3)
        c += 1

    c = 0
    toprow += 2

    for (id, group) in groups.items():
        worksheet.write(toprow,c,group["title"],fmt["basic_h"])
        toprow += 1
        worksheet.write_column(toprow,c,
                               [val[0] for (_, val) in group["rows"].items()])
        worksheet.write_column(toprow,c+1,
                               [val[1] for (_, val) in group["rows"].items()])
        for stat in edata["stats"]:
            if stat in ["min","max"] and id in ["seatSpec","expected","cmpSys"]:
                write_matrix(worksheet,toprow,c+2,
                             [row[stat] for row in edata[id]],fmt["base"],True)
            else:
                write_matrix(worksheet,toprow,c+2,
                             [row[stat] for row in edata[id]],
                             fmt["cell"],True,zeroesformat=fmt["base"])
            c += len(results["systems"]) + 1
        nrows = len(group["rows"])
        toprow += nrows + 1 if nrows > 0 else 0
        c = 0

    for r in range(len(results["systems"])):
        sheet_name  = results["systems"][r]["name"]
        worksheet   = workbook.add_worksheet(sheet_name[:31])
        worksheet.freeze_panes(10,2)
        parties = results["systems"][r]["parties"] + ["Total"]
        xtd_votes = add_totals(results["vote_table"]["votes"])
        xtd_shares = find_xtd_shares(xtd_votes)
        data_matrix = {
            "base": {
                "v" : xtd_votes,
                "vs": xtd_shares,
                "cs": results["base_allocations"][r]["xtd_const_seats"],
                "as": results["base_allocations"][r]["xtd_adj_seats"],
                "ts": results["base_allocations"][r]["xtd_total_seats"],
                "ss": results["base_allocations"][r]["xtd_seat_shares"],
                "id": results["base_allocations"][r]["xtd_ideal_seats"],
            }
        }
        list_measures = results["data"][r]["list_measures"]
        for stat in STATISTICS_HEADINGS.keys():
            data_matrix[stat] = {
                "v" : results["vote_data"][r]["sim_votes"][stat],
                "vs": results["vote_data"][r]["sim_shares"][stat],
                "cs": list_measures["const_seats"][stat],
                "as": list_measures["adj_seats"  ][stat],
                "ts": list_measures["total_seats"][stat],
                "ss": list_measures["seat_shares"][stat],
                "id": list_measures["ideal_seats"][stat],
            }
        alloc_info = [{
            "left_span": 2, "center_span": 4, "right_span": 1, "info": [
                {"label": "Allocation of constituency seats",
                    "rule": DRN[results["systems"][r]["primary_divider"]],
                    "threshold": (results["systems"][r]
                                  ["constituency_threshold"]/100.0)},
                {"label": "Apportionment of adjustment seats to parties",
                    "rule": DRN[results["systems"][r]["adj_determine_divider"]],
                    "threshold": (results["systems"][r]
                                  ["adjustment_threshold"]/100.0)},
                {"label": "Allocation of adjustment seats to lists",
                    "rule": DRN[results["systems"][r]["adj_alloc_divider"]],
                    "threshold": None}
            ]
        }, {
            "left_span": 2, "center_span": 3, "right_span": 0, "info": [
                {"label": "Allocation method for adjustment seats",
                    "rule": AMN[results["systems"][r]["adjustment_method"]]}
            ]
        }]

        toprow = 0
        c1 = 0
        c2 = c1 + 1
        worksheet.set_row_pixels(0,25)
        worksheet.set_column(c1,c1,25)
        worksheet.set_column(c2,c2,20)
        worksheet.write(toprow, c1, "Electoral system", fmt["h_big"])
        worksheet.write(toprow, c2, results["systems"][r]["name"], fmt["h_big"])
        toprow += 1
        worksheet.write(toprow, c2+1, "Rule", fmt["basic_h"])
        worksheet.write(toprow, c2+5, "Threshold", fmt["basic_h"])

        for group in alloc_info:
            toprow += 1
            c2 = c1 + group["left_span"]
            c3 = c2 + group["center_span"]
            for info in group["info"]:
                worksheet.write(toprow, c1, info["label"], fmt["basic"])
                worksheet.write(toprow, c2, info["rule"], fmt["basic"])
                if group["right_span"] > 0:
                    worksheet.write(toprow, c3, info["threshold"],
                                    fmt["threshold"])
                toprow += 1

        toprow += 1
        worksheet.set_row_pixels(toprow, 25)
        worksheet.write(toprow, c1, "Simulation results", fmt["h_big"])
        
        col = 2
        for table in tables:
            is_percentages_table = (
                table["heading"].endswith("shares") and
                not table["heading"].startswith("Reference"))
            worksheet.write(toprow, col, table["heading"], fmt["basic_h"])
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
            worksheet.write(toprow, 0, category["heading"], fmt["basic_h"])
            worksheet.write_column(toprow, 1, base_const_names, fmt["basic"])
            col = 2
            for table in tables:
                is_percentages_table = \
                    table["heading"].endswith("shares") and \
                    not table["heading"].startswith("Reference")
                draw_block(worksheet, row=toprow, col=col,
                    heading=table["heading"],
                    matrix=data_matrix[category["abbr"]][table["abbr"]],
                    cformat=category["cell_format"],
                    hideTotals=is_percentages_table
                )
                col += len(parties[:-1] if is_percentages_table else parties)+1
            toprow += len(base_const_names)+1

    workbook.close()

def votes_to_xlsx(matrix, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    fmt = prepare_formats(workbook)
    write_matrix(worksheet=worksheet, startrow=0, startcol=0,
        matrix=matrix, cformat=fmt["votes"])
    workbook.close()
