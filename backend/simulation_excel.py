"""Excel workbook writer for simulation results."""

from datetime import datetime

import numpy as np
import xlsxwriter

from dictionaries import EXCEL_HEADINGS, STATISTICS_HEADINGS, SCALING_NAMES
from measure_groups import MeasureGroups
from table_util import add_total, add_totals, find_percentages


SIMULATION_TABLES = [
    {"abbr": "v", "total": True, "heading": "Votes"},
    {"abbr": "vp", "total": False, "heading": "Vote percentages"},
    {"abbr": "rss", "total": True, "heading": "Reference seat shares"},
    {"abbr": "cs", "total": True, "heading": "Fixed seats"},
    {"abbr": "as", "total": True, "heading": "Adjustment seats"},
    {"abbr": "ts", "total": True, "heading": "Total seats"},
    {"abbr": "tsp", "total": False, "heading": "Total seat percentages"},
    {"abbr": "nmp", "total": True, "heading": "Negative margin percentages"},
    {"abbr": "nmc", "total": True, "heading": "Negative margin frequency"},
]

SUMMARY_TABLES = [
    {"abbr": "vp", "heading": "Vote percentages"},
    {"abbr": "rss", "heading": "Total reference seat shares"},
    {"abbr": "ts", "heading": "Total seats"},
    {"abbr": "ra", "heading": "Reference allocations"},
    {"abbr": "dis", "heading": "Disparity (excess if positive/deficiency if negative)"},
    {"abbr": "ovh", "heading": "Potential overhang"},
    {"abbr": "exs", "heading": "Excess (Positive disparity only)"},
    {"abbr": "sht", "heading": "Shortage (Negative disparity only)"},
]

CATEGORIES = [
    {"abbr": "base", "heading": "Values based on source votes"},
    {"abbr": "avg", "heading": "Avg. simulated values"},
    {"abbr": "min", "heading": "Minimum values"},
    {"abbr": "max", "heading": "Maximum values"},
    {"abbr": "std", "heading": "Standard deviations"},
]


class SimulationWorkbook:
    """Build the worksheets in a simulation-result workbook."""

    def __init__(self, results, filename, display_settings=None,
                 include_histogram_sheets=False):
        # Imported lazily by excel_util, so these shared helpers are initialized.
        from excel_util import prepare_formats

        self.results = results
        self.workbook = xlsxwriter.Workbook(filename)
        self.fmt = prepare_formats(self.workbook, display_settings)
        self.include_histogram_sheets = include_histogram_sheets
        self.systems = results["systems"]
        self.parties = self.systems[0]["parties"] + ["Total"]
        self.system_names = [system["name"] for system in self.systems]
        self.base_const_names = [
            constituency["name"]
            for constituency in results["vote_table"]["constituencies"]
        ] + ["Total"]
        party_info = results["vote_table"]["party_vote_info"]
        if party_info["specified"]:
            self.base_const_names.extend([party_info["name"], "Grand total"])

    def write(self):
        from excel_util import party_names_to_xlsx

        self.write_common_settings()
        self.write_quality_measures()
        self.write_allocation_summary()
        if self.include_histogram_sheets:
            self.write_histogram_sheets()
        for system_index in range(len(self.systems)):
            self.write_system_sheet(system_index)
        party_names_to_xlsx(
            self.workbook,
            self.fmt,
            self.results["vote_table"]["parties"],
            self.results["vote_table"].get("party_names"),
        )
        self.workbook.close()

    def draw_sim_block(
            self, worksheet, row, col, heading, data, abbreviation,
            total="hide"):
        from excel_util import write_matrix

        cell_format = (
            self.fmt["sim"] if abbreviation in {"avg", "std"}
            else self.fmt["base"])
        if heading.endswith("percentages"):
            cell_format = self.fmt["percentages"]
        elif heading.startswith("Reference seat"):
            cell_format = self.fmt["sim"]
        elif heading == "Votes":
            cell_format = self.fmt["base"]
        if total == "hide":
            data = [data_row[:-1] for data_row in data]
            totals_format = None
        else:
            totals_format = self.fmt["base"] if total == "integer" else cell_format
        write_matrix(
            worksheet, row, col, data, format=cell_format,
            display_zeros=True, totalsformat=totals_format)

    def simulation_settings(self):
        settings = self.results["sim_settings"]
        return [
            {"label": "Number of simulations", "data": self.results["iteration"]},
            {"label": "Random seed", "data": settings.get("random_seed", "")},
            {"label": "Generating method", "data": settings["gen_method"]},
            {"label": "Relative standard deviation for list votes",
             "data": settings["const_rsd"]},
            {"label": "Correlation between list votes within each party",
             "data": settings["const_corr"]},
            {"label": "Relative standard deviation for national party votes",
             "data": settings["party_vote_rsd"]},
            {"label": "Correlation between list votes and national party votes",
             "data": settings["party_vote_corr"]},
            {"label": "Thresholds used",
             "data": "yes" if settings["use_thresholds"] else "no"},
            {"label": "Scaling of votes for fractional reference seat shares",
             "data": SCALING_NAMES[settings["scaling"]]},
        ]

    def write_common_settings(self):
        worksheet = self.workbook.add_worksheet("Common settings")
        worksheet.set_column(0, 1, 43)
        worksheet.write(0, 0, "Date:", self.fmt["h"])
        worksheet.write(0, 1, datetime.now(), self.fmt["time"])
        vote_table = self.results["vote_table"]
        source = [
            ("Votes-and-seats table", vote_table["name"]),
            ("Number of constituencies", len(vote_table["constituencies"])),
            ("Number of parties", len(vote_table["parties"])),
            ("Total number of const. seats", sum(
                constituency["num_fixed_seats"]
                for constituency in vote_table["constituencies"])),
            ("Total number of adj. seats", sum(
                constituency["num_adj_seats"]
                for constituency in vote_table["constituencies"])),
            ("Total number of const. votes",
             sum(map(sum, vote_table["votes"])) + sum(vote_table.get("pruned", []))),
            ("Total number of national party votes",
             vote_table["party_vote_info"]["total"]),
        ]
        row = 2
        worksheet.write(row, 0, "Source votes and seats", self.fmt["h"])
        for label, value in source:
            row += 1
            worksheet.write(row, 0, label, self.fmt["basic"])
            worksheet.write(row, 1, value, self.fmt["basic"])
        row += 2
        worksheet.write(row, 0, "Simulation settings", self.fmt["h"])
        for setting in self.simulation_settings():
            row += 1
            worksheet.write(row, 0, setting["label"], self.fmt["basic"])
            worksheet.write(row, 1, setting["data"], self.fmt["basic"])

    def statistic_column_names(self, statistic):
        names = self.system_names.copy()
        if len(self.systems) >= 2 and statistic in {"avg", "lo95", "hi95"}:
            names.insert(2, "Difference")
        return names

    def quality_measure_data(self, groups):
        paired_data = self.results.get("paired_data", {})
        excluded = {"cmpList", "cmpParty", "cmpNationalDetails"}
        data = {"stats": EXCEL_HEADINGS.keys(), "stat_headings": EXCEL_HEADINGS}
        for group_id, group in groups.items():
            data[group_id] = []
            for measure in group["rows"]:
                row = {}
                for statistic in data["stats"]:
                    values = [
                        system["measures"][measure][statistic]
                        for system in self.results["data"]
                    ]
                    if (len(self.systems) >= 2
                            and statistic in {"avg", "lo95", "hi95"}):
                        difference = (
                            paired_data[measure][statistic]
                            if group_id not in excluded else None)
                        values.insert(2, difference)
                    row[statistic] = values
                data[group_id].append(row)
        return data

    def write_quality_measures(self):
        from excel_util import write_matrix

        party_votes = self.results["vote_table"]["party_vote_info"]["specified"]
        groups = MeasureGroups(self.systems, party_votes, "")
        data = self.quality_measure_data(groups)
        worksheet = self.workbook.add_worksheet("Quality measures")
        worksheet.freeze_panes(4, 2)
        worksheet.write(0, 0, "QUALITY MEASURES", self.fmt["h"])
        worksheet.write(1, 0, "Votes-and-seats table:", self.fmt["h"])
        worksheet.write(1, 1, self.results["vote_table"]["name"], self.fmt["basic"])
        worksheet.set_column(0, 0, 20)
        worksheet.write(
            3, 0,
            "Differences between allocated and fractional reference seats, "
            "summed over constituency lists",
            self.fmt["h"])
        worksheet.set_column(1, 1, 25)
        column = 2
        for statistic in data["stats"]:
            worksheet.write(2, column, data["stat_headings"][statistic], self.fmt["h"])
            names = self.statistic_column_names(statistic)
            worksheet.set_column(column, column + len(names) - 1, 11)
            for name in names:
                worksheet.write(3, column, name, self.fmt["h_center"])
                column += 1
            worksheet.set_column(column, column, 3)
            column += 1

        top = 4
        for group_id, group in groups.items():
            if group["title"]:
                worksheet.write(top, 0, group["title"], self.fmt["h"])
                top += 1
            worksheet.write_column(top, 0, [row[0] for row in group["rows"].values()])
            worksheet.write_column(top, 1, [row[1] for row in group["rows"].values()])
            column = 2
            for statistic in data["stats"]:
                base_format = (
                    statistic in {"min", "max"}
                    and group_id in {"seatSpec", "expected", "cmpList",
                                     "cmpParty", "cmpNationalDetails"})
                write_matrix(
                    worksheet, top, column,
                    [row[statistic] for row in data[group_id]],
                    format=self.fmt["base" if base_format else "cell"],
                    display_zeros=True)
                column += len(self.statistic_column_names(statistic)) + 1
            if group["rows"]:
                top += len(group["rows"]) + 1

    def national_vote_percentages(self):
        vote_table = self.results["vote_table"]
        constituency_totals = [sum(column) for column in zip(*vote_table["votes"])]
        percentages = []
        for system in self.systems:
            basis = system["seat_spec_options"]["party"]
            if basis == "totals":
                votes = constituency_totals
            elif basis == "party_vote_info":
                votes = vote_table["party_vote_info"]["votes"]
            else:
                assert basis == "average"
                national = vote_table["party_vote_info"]["votes"]
                votes = [(left + right) / 2
                         for left, right in zip(constituency_totals, national)]
            percentages.append([vote / sum(votes) for vote in votes])
        return percentages

    def allocation_summary_data(self):
        count = len(self.systems)
        allocations = self.results["base_allocations"]
        data = {
            "base": {
                "vp": self.national_vote_percentages(),
                "rss": [allocation["ref_seat_shares"][-1]
                        for allocation in allocations],
                "ts": [allocation["total_seats"][-1]
                       for allocation in allocations],
                "ra": [add_total(allocation["ref_seat_alloc"])
                       for allocation in allocations],
                "dis": [allocation["party_disparity"] for allocation in allocations],
                "ovh": [allocation["party_overhang"] for allocation in allocations],
                "exs": [allocation["party_excess"] for allocation in allocations],
                "sht": [allocation["party_shortage"] for allocation in allocations],
            }
        }
        party_measures = self.results["party_data"]
        for statistic in STATISTICS_HEADINGS:
            data[statistic] = {
                "vp": [party_measures[index]["nat_vote_percentages"][statistic]
                       for index in range(count)],
                "rss": [add_total(party_measures[index]["party_ref_seat_shares"][statistic])
                        for index in range(count)],
                "ts": [add_total(party_measures[index]["party_total_seats"][statistic])
                       for index in range(count)],
                "ra": [add_total(party_measures[index]["ref_seat_alloc"][statistic])
                       for index in range(count)],
                "dis": [party_measures[index]["party_disparity"][statistic]
                        for index in range(count)],
                "ovh": [party_measures[index]["party_overhang"][statistic]
                        for index in range(count)],
                "exs": [party_measures[index]["party_excess"][statistic]
                        for index in range(count)],
                "sht": [party_measures[index]["party_shortage"][statistic]
                        for index in range(count)],
            }
        return data

    @staticmethod
    def summary_has_no_total(table):
        heading = table["heading"]
        return (heading.endswith(("percentages", "overhang"))
                or heading.startswith(("Potential", "Disparity", "Excess", "Shortage")))

    def write_allocation_summary(self):
        worksheet = self.workbook.add_worksheet("Allocation summary")
        worksheet.freeze_panes(5, 2)
        worksheet.write(0, 0, "ALLOCATION SUMMARY", self.fmt["h"])
        worksheet.write(1, 0, "Votes-and-seats table:", self.fmt["h"])
        worksheet.write(1, 1, self.results["vote_table"]["name"], self.fmt["basic"])
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 25)
        worksheet.write(3, 1, "Electoral system", self.fmt["h"])
        column = 2
        for table in SUMMARY_TABLES:
            no_total = self.summary_has_no_total(table)
            worksheet.write(3, column, table["heading"], self.fmt["h"])
            worksheet.write_row(
                4, column, self.parties[:-1] if no_total else self.parties,
                self.fmt["h_center"])
            column += len(self.parties) + (0 if no_total else 1)
            worksheet.set_column(column - 1, column - 1, 3)

        data = self.allocation_summary_data()
        top = 5
        for category in CATEGORIES:
            skip_total = category["abbr"] in {"std", "min", "max"}
            worksheet.write(top, 0, category["heading"], self.fmt["h"])
            worksheet.write_column(top, 1, self.system_names, self.fmt["basic"])
            column = 2
            for table in SUMMARY_TABLES:
                no_total = self.summary_has_no_total(table)
                total = "hide" if skip_total and not no_total else "show"
                self.draw_sim_block(
                    worksheet, top, column, table["heading"],
                    data[category["abbr"]][table["abbr"]],
                    category["abbr"], total)
                column += len(self.parties) + (0 if no_total else 1)
            top += len(self.system_names) + 1

    def write_histogram_sheet(self, sheet_name, key, title, description):
        from excel_util import write_matrix

        worksheet = self.workbook.add_worksheet(sheet_name)
        party_count = len(self.parties) - 1
        data = np.reshape(
            self.results["histogram_data"][key],
            (len(self.systems), party_count))
        worksheet.write(0, 0, title, self.fmt["h"])
        worksheet.write(1, 0, description, self.fmt["h"])
        worksheet.write(2, 2, "Frequencies", self.fmt["h"])
        worksheet.write(3, 0, "System", self.fmt["h"])
        worksheet.set_column(1, 1, 15)
        worksheet.write(3, 1, f"{title} value", self.fmt["h_right"])
        worksheet.write_row(3, 2, self.parties[:-1], self.fmt["h_center"])
        row = 4
        for index, system in enumerate(self.systems):
            first = min(min(counts) for counts in data[index])
            last = max(max(counts) for counts in data[index])
            bins = range(first, last + 1)
            histogram = np.array([
                [counts.get(value, 0) for counts in data[index]]
                for value in bins
            ])
            worksheet.write(row, 0, system["name"], self.fmt["basic"])
            worksheet.write_column(row, 1, bins, self.fmt["base"])
            write_matrix(worksheet, row, 2, histogram, self.fmt["base"])
            row += len(bins) + 1

    def write_histogram_sheets(self):
        self.write_histogram_sheet(
            "Disparity data", "disparity_count", "Disparity",
            "Difference of Total seats of party minus its Reference allocation")
        self.write_histogram_sheet(
            "Overhang data", "overhang_count", "Overhang",
            "Positive values of fixed seats of party minus its reference allocation")

    def system_data(self, index, combined):
        votes = add_totals(self.results["vote_table"]["votes"])
        if self.results["vote_table"]["party_vote_info"]["specified"]:
            votes.append(add_total(
                self.results["vote_table"]["party_vote_info"]["votes"]))
        base = self.results["base_allocations"][index]
        data = {"base": {
            "v": votes,
            "vp": find_percentages(votes),
            "rss": base["ref_seat_shares"],
            "cs": base["fixed_seats"],
            "as": base["adj_seats"],
            "ts": base["total_seats"],
            "tsp": base["total_seat_percentages"],
            "nmp": base["neg_margins"],
            "nmc": base["neg_margin_count"],
        }}
        seat_measures = self.results["data"][index]["seat_measures"]
        vote_count = -1 if combined else len(
            self.results["vote_data"][index]["sim_votes"]["avg"])
        seat_count = -1 if combined else len(seat_measures["fixed_seats"]["avg"])
        for statistic in STATISTICS_HEADINGS:
            data[statistic] = {
                "v": self.results["vote_data"][index]["sim_votes"][statistic][
                    :vote_count],
                "vp": self.results["vote_data"][index]["sim_vote_percentages"][
                    statistic][:vote_count],
                "rss": seat_measures["ref_seat_shares"][statistic][:seat_count],
                "cs": seat_measures["fixed_seats"][statistic][:seat_count],
                "as": seat_measures["adj_seats"][statistic][:seat_count],
                "ts": seat_measures["total_seats"][statistic][:seat_count],
                "tsp": seat_measures["total_seat_percentages"][statistic][
                    :seat_count],
                "nmp": self.results["vote_data"][index]["neg_margin"][statistic],
                "nmc": self.results["vote_data"][index]["neg_margin_count"][statistic],
            }
        return data

    @staticmethod
    def allocation_info(system):
        from excel_util import (AMN, DRN, SCONST, SPARTY,
                                adjustment_qualification_text,
                                fixed_seat_threshold_text)

        return [
            {"left_span": 2, "center_span": 2, "right_span": 1, "info": [
                {"label": "Allocation of fixed seats:",
                 "rule": DRN[system["primary_divider"]],
                 "threshold": fixed_seat_threshold_text(system)},
                {"label": "Apportionment of adjustment seats to parties:",
                 "rule": DRN[system["adj_determine_divider"]],
                 "threshold": adjustment_qualification_text(system)},
                {"label": "Allocation of adjustment seats to lists:",
                 "rule": DRN[system["adj_alloc_divider"]], "threshold": None},
            ]},
            {"left_span": 2, "center_span": 2, "right_span": 0, "info": [
                {"label": "Allocation method for adjustment seats:",
                 "rule": AMN[system["adjustment_method"]]},
            ]},
            {"left_span": 2, "center_span": 2, "right_span": 0, "info": [
                {"label": "Specification of seat numbers:",
                 "rule": SCONST[system["seat_spec_options"]["const"]]},
            ]},
            {"left_span": 2, "center_span": 2, "right_span": 0, "info": [
                {"label": "Votes used as basis:",
                 "rule": SPARTY[system["seat_spec_options"]["party"]]},
            ]},
        ]

    def write_system_sheet(self, index):
        system = self.systems[index]
        combined = system["seat_spec_options"]["const"] == "one_const"
        worksheet = self.workbook.add_worksheet(system["name"][:31])
        worksheet.freeze_panes(10, 2)
        parties = system["parties"] + ["Total"]
        data = self.system_data(index, combined)
        worksheet.set_row_pixels(0, 25)
        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 20)
        worksheet.write(0, 0, "Electoral system:", self.fmt["h"])
        worksheet.write(0, 1, system["name"], self.fmt["basic"])
        worksheet.write(1, 0, "Votes-and-seats table:", self.fmt["h"])
        worksheet.write(1, 1, self.results["vote_table"]["name"], self.fmt["basic"])
        worksheet.write(2, 2, "Rule", self.fmt["h"])
        worksheet.write(2, 4, "Threshold", self.fmt["h"])
        top = 3
        for group in self.allocation_info(system):
            rule_column = group["left_span"]
            threshold_column = rule_column + group["center_span"]
            for info in group["info"]:
                worksheet.write(top, 0, info["label"], self.fmt["h"])
                worksheet.write(top, rule_column, info["rule"], self.fmt["basic"])
                if group["right_span"]:
                    worksheet.write(
                        top, threshold_column, info["threshold"], self.fmt["basic"])
                top += 1
        top += 1
        worksheet.set_row_pixels(top, 25)
        worksheet.write(top, 0, "Simulation results", self.fmt["h"])
        column = 2
        for table in SIMULATION_TABLES:
            worksheet.write(top, column, table["heading"], self.fmt["h"])
            worksheet.write_row(
                top + 1, column,
                parties if table["total"] else parties[:-1],
                self.fmt["h_center"])
            column += len(parties) + int(table["total"])
            worksheet.set_column(column - 1, column - 1, 3)
        top += 2
        worksheet.set_column(2, len(parties) + 1, 10)
        for category in CATEGORIES:
            worksheet.write(top, 0, category["heading"], self.fmt["h"])
            worksheet.write_column(top, 1, self.base_const_names, self.fmt["basic"])
            row = top
            if category["abbr"] != "base" and combined:
                row += len(self.base_const_names) - 1
            column = 2
            for table in SIMULATION_TABLES:
                self.draw_sim_block(
                    worksheet, row, column, table["heading"],
                    data[category["abbr"]][table["abbr"]],
                    category["abbr"], "show" if table["total"] else "hide")
                column += len(parties) + int(table["total"])
            top += len(self.base_const_names) + 1
