# coding:utf-8
"""
This module contains the core voting system logic.
"""

from table_util import entropy, add_totals, scale_matrix, add_total_column
from apportion import apportion1d_general
from electionSystem import ElectionSystem
from dictionaries import ADJUSTMENT_METHODS, DIVIDER_RULES, QUOTA_RULES
from dictionaries import CONSTANTS, DEMO_TABLE_FORMATS
import traceback as tb
from util import disp, subtract_m
from copy import deepcopy
from methods.nearest_to_previous import nearest_to_previous

class Election:
    """A single election."""

    def __init__(self, system, votes, party_vote_info, vote_table_name=''):
        self.system = system
        self.party_vote_info = party_vote_info
        self.set_votes(votes, party_vote_info["votes"])
        self.reference_results = []
        self.vote_table_name = vote_table_name

    def num_constituencies(self):
        return len(self.system["constituencies"])

    def num_parties(self):
        return len(self.system["parties"])

    def entropy(self):
        return entropy(self.m_votes, self.results['all_const_seats'], self.gen)

    def set_reference_results(self):
        self.reference_results = self.results['all_const_seats']

    def set_votes(self, votes, party_votes):
        # m_votes: Matrix of votes (numconst by numpart)
        # v_votes: Vector of votes (numpart, colsums of m_votes)
        self.party_vote_info["votes"] = deepcopy(party_votes)
        if self.num_constituencies() == 1:
            self.m_votes = [[sum(x) for x in zip(*votes)]]
        else:
            if len(votes) != self.num_constituencies():
                assert len(votes) == self.num_constituencies()
            self.m_votes = deepcopy(votes)
        assert all(len(row) == self.num_parties() for row in votes)
        self.v_votes = [sum(x) for x in zip(*votes)]

    @staticmethod
    def display_seats(allSeats, adjSeats):
        if adjSeats > 0:
            return f"{allSeats} ({adjSeats})"
        elif allSeats > 0:
            return f"{allSeats}"
        else:
            return ""

    def prepare_results(self):
        results = self.results
        votes = deepcopy(self.m_votes)
        votes.append(self.v_votes)

        row_names = [
            const["name"] for const in self.system["constituencies"]
        ] + ["Total"]
        all = deepcopy(results["all_const_seats"])
        all.append(results["all_const_total"])
        fix = deepcopy(results["fixed_const_seats"])
        fix.append(results["fixed_const_total"])
        adj = deepcopy(results["adj_const_seats"])
        adj.append(results["adj_const_total"])

        if self.party_vote_info["specified"]:
            votes.append(self.party_vote_info["votes"])
            all.append(results["all_nat_seats"])
            all.append(results["all_grand_total"])
            fix.append(results["fixed_nat_seats"])
            fix.append(results["fixed_grand_total"])
            row_names.append(self.party_vote_info["name"])
            row_names.append('Grand total')
            adj.append(results["adj_nat_seats"])
            adj.append(results["adj_grand_total"])

        all = add_total_column(all)
        adj = add_total_column(adj)
        fix = add_total_column(fix)
        votes = add_total_column(votes)

        seats = [[x[-1], y[-1], z[-1]] for (x,y,z) in zip (fix, adj, all)]

        self.results["votes"] = votes
        self.results["all"] = all
        self.results["adj"] = adj
        self.results["fix"] = fix
        self.results["row_names"] = row_names
        self.results["seats"] = seats

    def get_result_excel(self):
        return {
            "vote_table_name": self.vote_table_name,
            "system": self.system,
            "results": self.results,
            "demo_tables": self.demo_tables,
            "entropy": self.entropy()
        }

    def get_result_web(self):
        dispResult = []
        for (allrow, adjrow) in zip(self.results["all"], self.results["adj"]):
            dispRow = [self.display_seats(x,y) for (x,y) in zip(allrow, adjrow)]
            dispResult.append(dispRow)
        
        return {
            "voteless_seats":   self.voteless_seats(),
            "demo_tables":      self.demo_tables,
            "display_results":  dispResult
        }

    def run(self, use_thresholds=True):
        self.fixed_seats_alloc = []
        self.order = []
        self.desired_row_sums = [
            const["num_fixed_seats"] + const["num_adj_seats"]
            for const in self.system["constituencies"]
        ]
        party_vote_info = self.party_vote_info
        self.total_const_seats = sum(self.desired_row_sums)
        self.run_primary_apportionment(use_thresholds)
        self.run_determine_total_party_seats(use_thresholds)
        self.run_adjustment_apportionment()
        if party_vote_info["specified"] and party_vote_info["num_adj_seats"] > 0:
            self.add_national_adjustment_seats()

        self.prepare_results()
        return self.results['all_const_seats']

    def voteless_seats(self):
        over = [None]*self.num_constituencies()
        all_const_seats = self.results["all_const_seats"]
        for c in range(self.num_constituencies()):
            for p in range(self.num_parties()):
                over[c] = [r > 0 and v == CONSTANTS["minimum_votes"]
                           for (r, v) in zip(all_const_seats[c], self.m_votes[c])]
        return over

    def any_voteless(self):
        return any(v for x in self.voteless_seats() for v in x)

    def run_primary_apportionment(self, use_thresholds):
        """Conduct primary apportionment"""

        constituencies = self.system["constituencies"]
        threshold = self.system["constituency_threshold"] if use_thresholds else 0
        m_allocations = []
        self.last = []
        self.results = {}
        for i in range(self.num_constituencies()):
            num_seats = constituencies[i]["num_fixed_seats"]
            if num_seats != 0:
                alloc, _, last_in, _ = apportion1d_general(
                    v_votes = self.m_votes[i],
                    num_total_seats = num_seats,
                    prior_allocations=[],
                    rule = self.system.get_generator("primary_divider"),
                    type_of_rule = self.system.get_type("primary_divider"),
                    threshold_percent = threshold
                )
                assert last_in  # last_in is not None because num_seats > 0
                self.last.append(last_in)
            else:
                alloc = [0]*self.num_parties()
                self.last.append({'idx': None, 'active_votes': 0})
            m_allocations.append(alloc)

        v_allocations = [sum(x) for x in zip(*m_allocations)]
        self.results["fixed_const_total"] = deepcopy(v_allocations)

        if self.party_vote_info["specified"]:
            if self.party_vote_info["num_fixed_seats"] > 0:
                nat_fixed_alloc, _, _, _ = apportion1d_general(
                    v_votes = self.party_vote_info["votes"],
                    num_total_seats = self.party_vote_info["num_fixed_seats"],
                    prior_allocations = [],
                    rule = self.system.get_generator("primary_divider"),
                    type_of_rule = self.system.get_type("primary_divider"),
                    threshold_percent = threshold
                )
                for i in range(len(v_allocations)):
                    v_allocations[i] += nat_fixed_alloc[i]
            else:
                nat_fixed_alloc = [0]*len(self.party_vote_info["votes"])            
            self.results["fixed_nat_seats"] = nat_fixed_alloc
            
        self.results["fixed_const_seats"] = m_allocations
        self.results["fixed_grand_total"] = v_allocations

    def run_determine_total_party_seats(self, use_thresholds):
        """Calculate the number of adjustment seats each party gets."""
        opt = self.system["seat_spec_options"]["party"]
        if opt == "totals":
            votes = self.v_votes
        elif opt == "party_vote_info":
            votes = self.party_vote_info['votes']
        else:
            assert(opt=="average")
            votes = [(x+y)/2 for (x,y) in zip (self.v_votes, self.party_vote_info['votes'])]
        self.nat_votes = votes
        party_vote_info = self.party_vote_info
        nat_seats = (party_vote_info['num_fixed_seats'] + party_vote_info['num_adj_seats'])

        threshold = self.system["adjustment_threshold"] if use_thresholds else 0
        choice = self.system["adj_threshold_choice"] if use_thresholds else 0
        seats = self.system["adjustment_threshold_seats"] if use_thresholds else 0

        self.desired_col_sums, self.adj_seat_gen, _, _ \
            = apportion1d_general(
                v_votes = self.nat_votes,
                num_total_seats = self.total_const_seats + nat_seats,
                prior_allocations = self.results["fixed_const_total"],
                rule = self.system.get_generator("adj_determine_divider"),
                type_of_rule = self.system.get_type("adj_determine_divider"),
                threshold_percent = threshold,
                threshold_choice = choice,
                threshold_seats = seats
            )
        if self.party_vote_info["specified"]:
            self.desired_const_col_sums, _, _, _ \
                = apportion1d_general(
                    v_votes=self.nat_votes,
                    num_total_seats=self.total_const_seats,
                    prior_allocations=self.results["fixed_const_total"],
                    rule=self.system.get_generator("adj_determine_divider"),
                    type_of_rule=self.system.get_type("adj_determine_divider")
                )
        else:
            self.desired_const_col_sums = self.desired_col_sums

    def set_forced_reasons(self, demoTable):
        if "Criteria" in demoTable["headers"]:
            criteria_idx = demoTable["headers"].index("Criteria")
            for row in demoTable["steps"]:
                (constituency, party) = row[1:3]
                const = [c["name"] for c in self.system["constituencies"]]
                parties = self.system["parties"]
                constIdx = const.index(constituency)
                partyIdx = parties.index(party)
                if self.m_votes[constIdx][partyIdx] < 1:
                    row[criteria_idx] = "Forced allocation"
        return demoTable

    def run_adjustment_apportionment(self):
        """Conduct adjustment seat apportionment."""
        method = ADJUSTMENT_METHODS[self.system["adjustment_method"]]
        self.gen = self.system.get_generator("adj_alloc_divider")
        consts = self.system["constituencies"]
        self.method = method(m_votes=self.m_votes,
                             v_desired_row_sums=self.desired_row_sums,
                             v_desired_col_sums=self.desired_col_sums,
                             m_prior_allocations=self.results["fixed_const_seats"],
                             divisor_gen=self.gen, adj_seat_gen=self.adj_seat_gen,
                             v_fixed_seats=[con["num_fixed_seats"] for con in consts],
                             last=self.last)
        all_const_seats, self.demo_table_info = self.method
        adj_const_seats = subtract_m(
            all_const_seats, self.results["fixed_const_seats"])
        self.results["all_const_seats"] = all_const_seats
        self.results["adj_const_seats"] = adj_const_seats
        self.results["adj_const_total"] = [sum(x) for x in zip(*adj_const_seats)]
        self.results["all_const_total"] = [sum(x) for x in zip(*all_const_seats)]

        alloc_sequence = self.demo_table_info[0]
        self.demo_tables = []
        format = DEMO_TABLE_FORMATS[self.system["adjustment_method"]]
        format = [format] if len(self.demo_table_info) == 2 else format
        for i, print_demo_table in enumerate(self.demo_table_info[1:]):
            headers, steps, sup_header = print_demo_table(self.system, alloc_sequence)
            demo_table = {
                "headers":    headers,
                "steps":      steps,
                "sup_header": sup_header,
                "format":     format[i],
            }
            demo_table = self.set_forced_reasons(demo_table)
            self.demo_tables.append(demo_table)
        self.fix_special_formats()

    def add_national_adjustment_seats(self):
        self.results["adj_nat_seats"] = [
            x - y - z for (x,y,z) in
            zip(self.desired_col_sums,
                self.results["fixed_grand_total"],
                self.results["adj_const_total"])
        ]
        self.results["all_nat_seats"] = [
            x + y for (x,y) in
            zip(self.results["fixed_nat_seats"],
                self.results["adj_nat_seats"])
        ]
        self.results["adj_grand_total"] = [
            x + y for (x,y) in
            zip(self.results["adj_const_total"],
                self.results["adj_nat_seats"])
        ]
        self.results["all_grand_total"] = [
            x + y for (x,y) in
            zip(self.results["fixed_grand_total"],
                self.results["adj_grand_total"])
        ]

    def fix_special_formats(self):
        for table in self.demo_tables:
            fmtlist = list(table['format'])
            for j, f in enumerate(fmtlist):
                if f == 's' and any(table['steps']):
                    maxw = max(len(s[j]) for s in table['steps'])
                    fmtlist[j] = "c"  if maxw <= 2 else "l"
            table['format'] = "".join(fmtlist)

    def calculate_ideal_seats(self, scaling):
        import numpy as np, numpy.linalg as la
        scalar = float(self.total_const_seats)/sum(sum(x) for x in self.m_votes)
        ideal_seats = np.array(scale_matrix(self.m_votes, scalar))
        # assert self.solvable
        # rein = 0
        nrows = self.num_constituencies()
        ncols = self.num_parties()
        eta = np.ones(nrows)
        tau = np.ones(ncols)
        error = 1
        niter = 0
        col_sums = self.desired_const_col_sums
        if self.num_parties() > 1 and self.num_constituencies() > 1:
            row_constraints = scaling in {"both", "const"}
            col_constraints = scaling in {"both", "party"}
            if row_constraints and col_constraints:
                while round(error, 7) != 0.0:
                    error = 0
                    for c in range(nrows):
                        row_sum = self.desired_row_sums[c]
                        s = sum(ideal_seats[c, :])
                        eta = row_sum/s if s > 0 else 1
                        ideal_seats[c, :] *= eta
                        error = max(error, abs(1 - eta))
                    for p in range(ncols):
                        col_sum = col_sums[p]
                        s = sum(ideal_seats[:, p])
                        tau = col_sum/s if s > 0 else 1
                        ideal_seats[:, p] *= tau
                        error = max(error, abs(1 - tau))
            elif row_constraints:
                for c in range(self.num_constituencies()):
                    row_sum = self.desired_row_sums[c]
                    s = sum(ideal_seats[c, :])
                    eta = row_sum/s if s > 0 else 1
                    ideal_seats[c, :] *= eta
            elif col_constraints:
                for p in range(self.num_parties()):
                    col_sum = col_sums[p]
                    s = sum(ideal_seats[:, p])
                    tau = col_sum/s if s > 0 else 1
                    ideal_seats[:, p] *= tau
        self.ideal_seats = ideal_seats.tolist()
        if self.party_vote_info["specified"]:
            factor = sum(self.results["all_nat_seats"])/sum(self.nat_votes)
            self.ideal_nat_seats = [x*factor for x in self.nat_votes]
        else:
            self.ideal_nat_seats = None
