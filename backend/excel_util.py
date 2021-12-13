
import xlsxwriter
from datetime import datetime
from measure_groups import MeasureGroups

from table_util import m_subtract, add_totals, find_xtd_shares
from dictionaries import ADJUSTMENT_METHOD_NAMES as AMN, \
                         RULE_NAMES as DRN, \
                         GENERATING_METHOD_NAMES as GMN, \
                         STATISTICS_HEADINGS

def prepare_formats(workbook):
    formats = {}
    formats["cell"] = workbook.add_format()
    formats["cell"].set_align('right')
    formats["cell"].set_num_format('#,##0.000')

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

    formats["threshold"] = workbook.add_format()
    formats["threshold"].set_num_format('0%')
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
    formats["step_h"].set_text_wrap()
    formats["step_h"].set_align('center')

    formats["step"] = workbook.add_format()
    formats["step"].set_text_wrap()
    formats["step"].set_align('center')

    formats["inter_h"] = workbook.add_format()
    formats["inter_h"].set_align('left')
    formats["inter_h"].set_bold()
    formats["inter_h"].set_italic()
    formats["inter_h"].set_font_size(11)

    formats["base"] = workbook.add_format()
    formats["base"].set_num_format('#,##0')

    formats["sim"] = workbook.add_format()
    formats["sim"].set_num_format('#,##0.000')

    return formats

def write_matrix(worksheet, startrow, startcol, matrix, cformat, display_zeroes=False, totalsformat = None, zeroesformat = None):
    for c in range(len(matrix)):
        if totalsformat is not None:
            for p in range(len(matrix[c])-1):
                if matrix[c][p] != 0 or display_zeroes:
                    try:
                        worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        cformat[c])
                    except TypeError:
                        if matrix[c][p] == 0 and zeroesformat is not None:
                            worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        zeroesformat)
                        else:
                            worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        cformat)
            worksheet.write(startrow+c, startcol+len(matrix[c])-1, matrix[c][-1],
                        totalsformat)
        else:
            for p in range(len(matrix[c])):
                if matrix[c][p] != 0 or display_zeroes:
                    try:
                        worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        cformat[c])
                    except TypeError:
                        if matrix[c][p] == 0 and zeroesformat is not None:
                            worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        zeroesformat)
                        else:
                            worksheet.write(startrow+c, startcol+p, matrix[c][p],
                                        cformat)

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
        worksheet.merge_range(
            row, col, row, col+len(xheaders), heading, fmt["h"])
        worksheet.write(row+1, col, topleft, fmt["basic"])
        worksheet.write_row(row+1, col+1, xheaders, fmt["center"])
        worksheet.write_column(row+2, col, yheaders, fmt["basic"])
        write_matrix(worksheet, row+2, col+1, matrix, cformat)

    for r in range(len(elections)):
        election = elections[r]
        system = election.system
        sheet_name = f'{r+1}-{system["name"]}'
        worksheet = workbook.add_worksheet(sheet_name[:31])
        worksheet.set_column(0,0, 30)
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
        xtd_final_votes = add_totals([election.v_votes_eliminated])[0]
        xtd_final_shares = find_xtd_shares([xtd_final_votes])[0]

        date_label = "Date:"
        info_groups = [
            {"left_span": 1, "right_span": 2, "info": [
                {"label": date_label,
                    "data": datetime.now()},
                {"label": "Vote table:",
                    "data": election.name},
                {"label": "Electoral system:",
                    "data": system["name"]},
            ]},
            {"left_span": 4, "right_span": 2, "info": [
                {"label": "Rule for allocating constituency seats:",
                    "data": DRN[system["primary_divider"]]},
                {"label": "Threshold for constituency seats:",
                    "data": system["constituency_threshold"]},
                {"label": "Rule for apportioning adjustment seats:",
                    "data": DRN[system["adj_determine_divider"]]},
                {"label": "Threshold for apportioning adjustment seats:",
                    "data": system["adjustment_threshold"]},
                {"label": "Rule for allocating adjustment seats:",
                    "data": DRN[system["adj_alloc_divider"]]},
                {"label": "Method for allocating adjustment seats:",
                    "data": AMN[system["adjustment_method"]]}
            ]},
        ]

        toprow = 0
        startcol = 0
        bottomrow = toprow
        c1=startcol
        #Basic info
        for group in info_groups:
            row = toprow
            c2 = c1 + group["left_span"]
            for info in group["info"]:
                if group["left_span"] == 1:
                    worksheet.write(row,c1,info["label"],fmt["basic_h"])
                else:
                    worksheet.merge_range(row,c1,row,c2-1,info["label"],fmt["basic_h"])
                if info["label"] == date_label:
                    worksheet.write(row,c2,info["data"],fmt["time"])
                else:
                    worksheet.write(row,c2,info["data"],fmt["basic"])
                row += 1
            bottomrow = max(row, bottomrow)
            c1 = c2 + group["right_span"]

        draw_block(worksheet, row=toprow, col=c1+1,
            heading="Required number of seats",
            xheaders=["Const.", "Adj.", "Total"],
            yheaders=const_names,
            matrix=add_totals([
                [const["num_const_seats"],const["num_adj_seats"]]
                for const in system["constituencies"]
            ]),
            cformat=fmt["base"]
        )
        bottomrow = max(2+len(const_names), bottomrow)
        toprow = bottomrow+2

        col = startcol
        draw_block(worksheet, row=toprow, col=col,
            heading="Votes", xheaders=parties, yheaders=const_names,
            matrix=xtd_votes, cformat=fmt["base"]
        )
        col += len(parties)+2
        draw_block(worksheet, row=toprow, col=col,
            heading="Vote percentages", xheaders=parties, yheaders=const_names,
            matrix=xtd_shares
        )
        toprow += len(const_names)+3
        col = startcol
        draw_block(worksheet, row=toprow, col=col,
            heading="Constituency seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_const_seats, cformat=fmt["base"]
        )
        toprow += len(const_names)+3

        row_headers = ['Total votes', 'Vote shares', 'Threshold',
                       'Votes above threshold',
                       'Vote shares above threshold', 'Constituency seats']
        matrix = [xtd_votes[-1],   xtd_shares[-1],   [threshold],
                  xtd_final_votes, xtd_final_shares, xtd_const_seats[-1]]
        formats = [fmt["base"], fmt["share"], fmt["share"],
                   fmt["base"], fmt["share"], fmt["base"]]
        draw_block(worksheet, row=toprow, col=startcol,
            heading="Adjustment seat apportionment", topleft="Party",
            xheaders=parties, yheaders=row_headers,
            matrix=matrix, cformat=formats
        )
        toprow += len(row_headers)+3

        h = election.demonstration_table["headers"]
        data = election.demonstration_table["steps"]
        worksheet.merge_range(
            toprow, startcol,
            toprow, startcol+len(parties),
            "Allocation of adjustment seats step-by-step", fmt["h"]
        )
        toprow += 1
        worksheet.write_row(toprow, startcol, h, fmt["step_h"])
        toprow += 1
        for i in range(len(data)):
            worksheet.write_row(toprow, startcol, data[i], fmt["step"])
            toprow += 1
        toprow += 1

        col = startcol
        draw_block(worksheet, row=toprow, col=col,
            heading="Adjustment seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_adj_seats, cformat=fmt["base"]
        )
        toprow += len(const_names)+3
        draw_block(worksheet, row=toprow, col=col,
            heading="Total seats", xheaders=parties, yheaders=const_names,
            matrix=xtd_total_seats, cformat=fmt["base"]
        )
        col += len(parties)+2
        draw_block(worksheet, row=toprow, col=col,
            heading="Seat shares", xheaders=parties, yheaders=const_names,
            matrix=xtd_seat_shares
        )
        toprow += len(const_names)+3
        col = startcol

        worksheet.write(toprow, startcol, 'Entropy:', fmt["h"])
        worksheet.write(toprow, startcol+1, election.entropy(), fmt["cell"])

    workbook.close()

def simulation_to_xlsx(simulation, filename):
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
        if heading.lower().startswith("ideal") or heading.lower().startswith("reference"):
            cformat = fmt["cell"]
            totalsformat = fmt["base"]
        if heading == "Votes":
            cformat = fmt["base"]
        write_matrix(worksheet, row, col, matrix, cformat, False, totalsformat)

    row_constraints = simulation.sim_settings["scaling"] in {"both","const"} and simulation.num_parties > 1
    col_constraints = simulation.sim_settings["scaling"] in {"both","party"} and simulation.num_constituencies > 1
    gen_method = next((g["text"] for g in GMN if g["value"]=='gamma'),None)
    sim_settings = [
        {"label": "Number of simulations run",
            "data": simulation.iteration},
        {"label": "Generating method",
            "data": gen_method},
        {"label": "Coefficient of variation",
            "data": simulation.var_coeff},
        {"label": "Apply randomness to",
            "data": "All constituencies" if simulation.apply_random == -1 else None},
        {"label": "Scaling of reference seat shares",
            "data": "within both constituencies and parties" if row_constraints and col_constraints
            else "within constituencies" if row_constraints
            else "within parties" if col_constraints
            else None}
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
    worksheet.write(row, c2, simulation.vote_table["name"], fmt["basic"])
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
    base_const_names = [const["name"] for const in simulation.constituencies]\
                        + ["Total"]

    #Measures
    results = simulation.get_results_dict()
    data = results["data"]
    systems = results["systems"]
    groups = MeasureGroups(systems)
    stats = ["avg", "min", "max", "std", "skw", "kur"]
    edata = {}
    edata["stats"] = stats
    edata["stat_headings"] = STATISTICS_HEADINGS

    for (id, group) in groups.items():
        edata[id] = []
        for (measure, _) in group["rows"].items():
            row = {}
            for stat in stats:
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

    for stat in stats:
        worksheet.write(toprow,c,edata["stat_headings"][stat],fmt["basic_h"])
        worksheet.set_column(c,c+len(simulation.systems)-1,15)
        for system in simulation.systems:
            worksheet.write(toprow+1,c,system["name"],fmt["h_center"])
            c += 1
        worksheet.set_column(c,c,3)
        c += 1

    c = 0
    toprow += 2

    for (id, group) in groups.items():
        worksheet.write(toprow,c,group["title"],fmt["basic_h"])
        toprow += 1
        worksheet.write_column(toprow,c,[val[0] for (_, val) in group["rows"].items()])
        worksheet.write_column(toprow,c+1,[val[1] for (_, val) in group["rows"].items()])
        
        for stat in stats:
            if stat in ["min","max"] and id in ["seatSpec","expected","cmpSys"]:
                write_matrix(worksheet,toprow,c+2,[row[stat] for row in edata[id]],fmt["base"],True)
            else:
                write_matrix(worksheet,toprow,c+2,[row[stat] for row in edata[id]],fmt["cell"],True,zeroesformat=fmt["base"])
            c += len(simulation.systems) + 1
        nrows = len(group["rows"])
        toprow += nrows + 1 if nrows > 0 else 0
        c = 0

    for r in range(len(simulation.systems)):
        sheet_name  = simulation.systems[r]["name"]
        worksheet   = workbook.add_worksheet(sheet_name[:31])
        worksheet.freeze_panes(10,2)
        parties = simulation.systems[r]["parties"] + ["Total"]
        data_matrix = {
            "base": {
                "v" : simulation.xtd_votes,
                "vs": simulation.xtd_vote_shares,
                "cs": simulation.base_allocations[r]["xtd_const_seats"],
                "as": simulation.base_allocations[r]["xtd_adj_seats"],
                "ts": simulation.base_allocations[r]["xtd_total_seats"],
                "ss": simulation.base_allocations[r]["xtd_seat_shares"],
                "id": simulation.base_allocations[r]["xtd_ideal_seats"],
            },
            "avg": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["avg"],
                "vs": simulation.list_data[-1]["sim_shares" ]["avg"],
                "cs": simulation.list_data[ r]["const_seats"]["avg"],
                "as": simulation.list_data[ r]["adj_seats"  ]["avg"],
                "ts": simulation.list_data[ r]["total_seats"]["avg"],
                "ss": simulation.list_data[ r]["seat_shares"]["avg"],
                "id": simulation.list_data[ r]["ideal_seats"]["avg"],
            },
            "std": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["std"],
                "vs": simulation.list_data[-1]["sim_shares" ]["std"],
                "cs": simulation.list_data[ r]["const_seats"]["std"],
                "as": simulation.list_data[ r]["adj_seats"  ]["std"],
                "ts": simulation.list_data[ r]["total_seats"]["std"],
                "ss": simulation.list_data[ r]["seat_shares"]["std"],
                "id": simulation.list_data[ r]["ideal_seats"]["std"],
            },
            "min": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["min"],
                "vs": simulation.list_data[-1]["sim_shares" ]["min"],
                "cs": simulation.list_data[ r]["const_seats"]["min"],
                "as": simulation.list_data[ r]["adj_seats"  ]["min"],
                "ts": simulation.list_data[ r]["total_seats"]["min"],
                "ss": simulation.list_data[ r]["seat_shares"]["min"],
                "id": simulation.list_data[ r]["ideal_seats"]["min"],
            },
            "max": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["max"],
                "vs": simulation.list_data[-1]["sim_shares" ]["max"],
                "cs": simulation.list_data[ r]["const_seats"]["max"],
                "as": simulation.list_data[ r]["adj_seats"  ]["max"],
                "ts": simulation.list_data[ r]["total_seats"]["max"],
                "ss": simulation.list_data[ r]["seat_shares"]["max"],
                "id": simulation.list_data[ r]["ideal_seats"]["max"],
            },
            "skw": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["skw"],
                "vs": simulation.list_data[-1]["sim_shares" ]["skw"],

                "cs": simulation.list_data[ r]["const_seats"]["skw"],
                "as": simulation.list_data[ r]["adj_seats"  ]["skw"],
                "ts": simulation.list_data[ r]["total_seats"]["skw"],
                "ss": simulation.list_data[ r]["seat_shares"]["skw"],
                "id": simulation.list_data[ r]["ideal_seats"]["skw"],
            },
            "kur": {
                "v" : simulation.list_data[-1]["sim_votes"  ]["kur"],
                "vs": simulation.list_data[-1]["sim_shares" ]["kur"],
                "cs": simulation.list_data[ r]["const_seats"]["kur"],
                "as": simulation.list_data[ r]["adj_seats"  ]["kur"],
                "ts": simulation.list_data[ r]["total_seats"]["kur"],
                "ss": simulation.list_data[ r]["seat_shares"]["kur"],
                "id": simulation.list_data[ r]["ideal_seats"]["kur"],
            },
        }

        alloc_info = [{
            "left_span": 2, "center_span": 4, "right_span": 1, "info": [
                {"label": "Allocation of constituency seats",
                    "rule": DRN[simulation.systems[r]["primary_divider"]],
                    "threshold": simulation.systems[r]["constituency_threshold"]/100.0},
                {"label": "Apportionment of adjustment seats to parties",
                    "rule": DRN[simulation.systems[r]["adj_determine_divider"]],
                    "threshold": simulation.systems[r]["adjustment_threshold"]/100.0},
                {"label": "Allocation of adjustment seats to lists",
                    "rule": DRN[simulation.systems[r]["adj_alloc_divider"]],
                    "threshold": None}
            ]
        }, {
            "left_span": 2, "center_span": 3, "right_span": 0, "info": [
                {"label": "Allocation method for adjustment seats",
                    "rule": AMN[simulation.systems[r]["adjustment_method"]]}
            ]
        }]

        toprow = 0
        c1 = 0
        c2 = c1 + 1
        worksheet.set_row_pixels(0,25)
        worksheet.set_column(c1,c1,25)
        worksheet.set_column(c2,c2,20)
        worksheet.write(toprow, c1, "Electoral system", fmt["h_big"])
        worksheet.write(toprow, c2, simulation.systems[r]["name"], fmt["h_big"])
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
                    worksheet.write(toprow, c3, info["threshold"], fmt["threshold"])
                toprow += 1

        toprow += 1
        worksheet.set_row_pixels(toprow, 25)
        worksheet.write(toprow, c1, "Simulation results", fmt["h_big"])
        
        col = 2
        for table in tables:
            is_percentages_table = table["heading"].endswith("shares") and not table["heading"].startswith("Reference")
            worksheet.write(toprow, col, table["heading"], fmt["basic_h"])
            worksheet.write_row(toprow+1, col, parties[:-1] if is_percentages_table else parties, fmt["h_center"])
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
                is_percentages_table = table["heading"].endswith("shares") and not table["heading"].startswith("Reference")
                draw_block(worksheet, row=toprow, col=col,
                    heading=table["heading"],
                    matrix=data_matrix[category["abbr"]][table["abbr"]],
                    cformat=category["cell_format"],
                    hideTotals=is_percentages_table
                )
                col += len(parties[:-1] if is_percentages_table else parties)+1
            toprow += len(base_const_names)+1

    workbook.close()

def save_votes_to_xlsx(matrix, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    fmt = prepare_formats(workbook)
    write_matrix(worksheet=worksheet, startrow=0, startcol=0,
        matrix=matrix, cformat=fmt["cell"])
    workbook.close()
