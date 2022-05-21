#coding:utf-8
"""
This module contains the core voting system logic.
"""
from tabulate import tabulate

from table_util import entropy, add_totals, scale_matrix
from apportion import apportion1d_general, \
    threshold_elimination_totals, threshold_elimination_constituencies
from electionSystem import ElectionSystem
from dictionaries import ADJUSTMENT_METHODS, DIVIDER_RULES, QUOTA_RULES
from dictionaries import CONSTANTS, DEMO_TABLE_FORMATS
import traceback as tb
from util import disp, subtract_m
from copy import deepcopy
from methods.nearest_to_previous import nearest_to_previous

def display_seats(totSeats, adjSeats):
    if adjSeats > 0:
        return f"{totSeats} ({adjSeats})"
    elif totSeats > 0:
        return f"{totSeats}"
    else:
        return ""

class Election:
    """A single election."""
    def __init__(self, system, votes, min_votes=0, name=''):
        self.system = system
        self.set_votes(votes, min_votes=min_votes)
        self.reference_results = []
        self.name = name

    def num_constituencies(self):
        return len(self.system["constituencies"])

    def num_parties(self):
        return len(self.system["parties"])

    def entropy(self):
        return entropy(self.m_votes, self.results, self.gen)

    def set_reference_results(self):
        self.reference_results = self.results

    def set_votes(self, votes, min_votes=0):
        # m_votes: Matrix of votes (numconst by numpart)
        # v_votes: Vector of votes (numpart, colsums of m_votes)
        if self.num_constituencies() == 1:
            self.m_votes = [[sum(x) for x in zip(*votes)]]
        else:
            if len(votes) != self.num_constituencies():
                assert len(votes) == self.num_constituencies()
            self.m_votes = deepcopy(votes)
        assert all(len(row) == self.num_parties() for row in votes)
        self.v_votes = [sum(x) for x in zip(*votes)]

    def display_results(self):
        dispResult = []
        totSeats = add_totals(self.results)
        adjSeats = add_totals(self.m_adj_seats)
        for (totrow, adjrow) in zip(totSeats, adjSeats):
            dispRow = [display_seats(r,a) for (r,a) in zip(totrow, adjrow)]
            dispResult.append(dispRow)
        return dispResult

    def get_result_dict(self):
        # if not self.solvable:
        #     return None
        return {
            "voteless_seats": self.voteless_seats(),
            "seat_allocations": add_totals(self.results),
            "demo_tables": self.demo_tables,
            "display_results": self.display_results()
        }

    def run(self, threshold=True):
        # Run an election based on current systems and votes.
        # Return None if no solution exists.

        # How many constituency seats does each party get in each constituency
        self.const_seats_alloc = []

        # Which seats does each party get in each constituency:
        self.order = []

        # Determine total seats (const + adjustment) in each constituency:
        self.v_desired_row_sums = [
            const["num_const_seats"] + const["num_adj_seats"]
            for const in self.system["constituencies"]
        ]

        # Determine total seats in play:
        self.total_seats = sum(self.v_desired_row_sums)

        self.run_primary_apportionment()
        if threshold:
            self.run_threshold_elimination()
        self.run_determine_adjustment_seats()
        self.run_adjustment_apportionment()
        # if not self.solvable:
        #     self.results = None
        return self.results

    @staticmethod
    def anym(A):
        # is any element of matrix A true?
        return any(any(a) for a in A)

    def voteless_seats(self):
        over = [None]*self.num_constituencies()
        for c in range(self.num_constituencies()):
            for p in range(self.num_parties()):
                over[c] = [r > 0 and v == CONSTANTS["minimum_votes"]
                           for (r,v) in zip(self.results[c], self.m_votes[c])]
        return over

    def any_voteless(self):
        return any(v for x in self.voteless_seats() for v in x)

    def run_primary_apportionment(self):
        """Conduct primary apportionment"""

        constituencies = self.system["constituencies"]
        parties = self.system["parties"]

        m_allocations = []
        self.last = []
        for i in range(self.num_constituencies()):
            num_seats = constituencies[i]["num_const_seats"]
            if num_seats != 0:
                alloc, _, last_in, _ = apportion1d_general(
                    v_votes=self.m_votes[i],
                    num_total_seats=num_seats,
                    prior_allocations=[],
                    rule=self.system.get_generator("primary_divider"),
                    type_of_rule=self.system.get_type("primary_divider"),
                    threshold=self.system["constituency_threshold"]
                )
                assert last_in #last_in is not None because num_seats > 0
                self.last.append(last_in)
            else:
                alloc = [0]*self.num_parties()
                self.last.append({'idx':None, 'active_votes':0})
            m_allocations.append(alloc)
            # self.order.append(seats)

        # Useful:
        # print tabulate([[parties[x] for x in y] for y in self.order])

        v_allocations = [sum(x) for x in zip(*m_allocations)]

        self.m_const_seats = m_allocations
        self.v_const_seats_alloc = v_allocations

    def run_threshold_elimination(self):
        """Eliminate parties that do not reach the adjustment threshold."""
        self.m_votes_eliminated = threshold_elimination_constituencies(
            votes=self.m_votes,
            threshold=self.system["adjustment_threshold"]
        )
        self.v_votes_eliminated = threshold_elimination_totals(
            votes=self.m_votes,
            threshold=self.system["adjustment_threshold"]
        )

    def run_determine_adjustment_seats(self):
        """Calculate the number of adjustment seats each party gets."""
        self.v_desired_col_sums, self.adj_seat_gen, _, _ \
            = apportion1d_general(
                v_votes=self.v_votes,
                num_total_seats=self.total_seats,
                prior_allocations=self.v_const_seats_alloc,
                rule=self.system.get_generator("adj_determine_divider"),
                type_of_rule=self.system.get_type("adj_determine_divider"),
                threshold=self.system["adjustment_threshold"]
            )
        return self.v_desired_col_sums

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
        self.results, self.demo_table_info = method (
                m_votes             = self.m_votes_eliminated,
                v_desired_row_sums  = self.v_desired_row_sums,
                v_desired_col_sums  = self.v_desired_col_sums,
                m_prior_allocations = self.m_const_seats,
                divisor_gen         = self.gen,
                adj_seat_gen        = self.adj_seat_gen,
                threshold           = self.system["adjustment_threshold"],
                orig_votes          = self.m_votes,
                v_const_seats       = [con["num_const_seats"] for con in consts],
                last                = self.last
            )
        self.m_adj_seats = subtract_m(self.results, self.m_const_seats)
        v_results = [sum(x) for x in zip(*self.results)]
        devs = [abs(a-b) for a, b in zip(self.v_desired_col_sums, v_results)]
        self.adj_dev = sum(devs)

        alloc_sequence = self.demo_table_info[0]
        self.demo_tables = []
        format = DEMO_TABLE_FORMATS[self.system["adjustment_method"]]
        format = [format] if len(self.demo_table_info) == 2 else format
        for i, print_demo_table in enumerate(self.demo_table_info[1:]):
            headers, steps, sup_header = print_demo_table(self.system, alloc_sequence)
            demo_table = {
                "headers": headers,
                "steps": steps,
                "sup_header": sup_header,
                "format": format[i],
            }
            demo_table = self.set_forced_reasons(demo_table)
            self.demo_tables.append(demo_table)
        self.fix_special_formats()

    def fix_special_formats(self):
        for table in self.demo_tables:
            fmtlist = list(table['format'])
            for j,f in enumerate(fmtlist):
                if f=='s' and any(table['steps']):
                    maxw = max(len(s[j]) for s in table['steps'])
                    fmtlist[j] = "c" if maxw <= 2 else "l"
            table['format'] = "".join(fmtlist)

    def calculate_ideal_seats(self, scaling):
        scalar = float(self.total_seats)/sum(sum(x) for x in self.m_votes)
        ideal_seats = scale_matrix(self.m_votes, scalar)
        # assert self.solvable
        rein = 0
        error = 1
        niter = 0
        if self.num_parties() > 1 and self.num_constituencies() > 1:
            row_constraints = scaling in {"both", "const"}
            col_constraints = scaling in {"both", "party"}
            while round(error, 7) != 0.0: #TODO look at this
                niter += 1
                error = 0
                if row_constraints:
                    for c in range(self.num_constituencies()):
                        s = sum(ideal_seats[c])
                        if s != 0:
                            mult = float(self.v_desired_row_sums[c])/s
                            error += abs(1 - mult)
                            mult += rein*(1 - mult)
                            for p in range(self.num_parties()):
                                ideal_seats[c][p] *= mult
                if col_constraints:
                    for p in range(self.num_parties()):
                        s = sum([c[p] for c in ideal_seats])
                        if s != 0:
                            mult = float(self.v_desired_col_sums[p])/s
                            error += abs(1 - mult)
                            mult += rein*(1 - mult)
                            for c in range(self.num_constituencies()):
                                ideal_seats[c][p] *= mult
        self.ideal_seats = ideal_seats

