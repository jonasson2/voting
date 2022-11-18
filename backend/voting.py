# coding:utf-8
"""
This module contains the core voting system logic.
"""

from table_util import entropy, add_total_column
from apportion import apportion1d_general
from dictionaries import ADJUSTMENT_METHODS, DIVIDER_RULES, QUOTA_RULES
from dictionaries import DEMO_TABLE_FORMATS
from util import disp, subtract_m
from copy import deepcopy
import numpy as np

class Election:
    """A single election."""

    def __init__(self, system, votes, party_vote_info, vote_table_name=''):
        self.system = system
        self.party_vote_info = party_vote_info
        self.party_votes = np.array(party_vote_info["votes"])
        self.set_votes(votes)
        self.reference_results = []
        self.vote_table_name = vote_table_name
        self.stored_entropy = None

    def num_constituencies(self):
        return len(self.system["constituencies"])

    def num_parties(self):
        return len(self.system["parties"])

    def entropy(self):
        if self.stored_entropy is None:
            self.stored_entropy = entropy(self.votes, self.results['all_const_seats'],
                                          self.gen)
        return self.stored_entropy

    def set_reference_results(self):
        self.reference_results = self.results['all_const_seats']

    def set_votes(self, votes, party_votes=None):
        # votesums: column sums of m_votes
        if party_votes:
            self.party_votes = np.array(party_votes)
        if self.num_constituencies() == 1:
            self.votes = votes.sum(0)[None,:]
        else:
            assert len(votes) == self.num_constituencies()
            self.votes = np.array(votes)
        assert all(len(row) == self.num_parties() for row in votes)
        self.votesums = self.votes.sum(0)

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
        votes = self.votes.tolist()
        votes.append(self.votesums.tolist())

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
            votes.append(self.nat_votes.tolist())
            #TODO:  kemur villa ef reynt er að bæta við lista af strengjum, bæta frekar við lista af atkvæðum notuðum til grundvallar?
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
        if party_vote_info["specified"]:
            self.add_national_adjustment_seats()
        else:
            self.results['all_grand_total'] = self.results['all_const_total']

        self.prepare_results()
        return self.results['all_const_seats']

    def voteless_seats(self):
        over = [None]*self.num_constituencies()
        all_const_seats = self.results["all_const_seats"]
        for c in range(self.num_constituencies()):
            for p in range(self.num_parties()):
                over[c] = [r > 0 and float(v) == 0
                           for (r, v) in zip(all_const_seats[c], self.votes[c])]
        return over

    def any_voteless(self):
        return any(v for x in self.voteless_seats() for v in x)

    def run_primary_apportionment(self, use_thresholds):
        constituencies = self.system["constituencies"]
        threshold = self.system["constituency_threshold"] if use_thresholds else 0
        m_allocations = []
        self.last = []
        self.results = {}
        for i in range(self.num_constituencies()):
            num_seats = constituencies[i]["num_fixed_seats"]
            if num_seats != 0:
                alloc, _, last_in, _ = apportion1d_general(
                    v_votes = self.votes[i],
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

        opt = self.system["seat_spec_options"]["party"]
        if opt == "totals":
            votes = self.votesums
        elif opt == "party_vote_info":
            votes = self.party_votes
        else:
            assert (opt == "average")
            votes = (self.votes_sums + self.party_votes)/2
        self.nat_votes = votes

        if self.party_vote_info["specified"]:
            if self.system["nat_seats"]["num_fixed_seats"] > 0:
                nat_fixed_alloc, _, _, _ = apportion1d_general(
                    v_votes = self.nat_votes,
                    num_total_seats = self.system["nat_seats"]["num_fixed_seats"],
                    prior_allocations = [],
                    rule = self.system.get_generator("primary_divider"),
                    type_of_rule = self.system.get_type("primary_divider"),
                    threshold_percent = threshold
                )
                for i in range(len(v_allocations)):
                    v_allocations[i] += nat_fixed_alloc[i]
            else:
                nat_fixed_alloc = [0]*len(self.party_votes)
            self.results["fixed_nat_seats"] = nat_fixed_alloc
            
        self.results["fixed_const_seats"] = m_allocations
        self.results["fixed_grand_total"] = v_allocations

    def run_determine_total_party_seats(self, use_thresholds):
        """Calculate the number of adjustment seats each party gets."""
        nat_seats = ((self.system["nat_seats"]['num_fixed_seats'] +
                      self.system["nat_seats"]['num_adj_seats']) \
                         if self.party_vote_info['specified'] else 0)

        threshold = self.system["adjustment_threshold"] if use_thresholds else 0
        choice = self.system["adj_threshold_choice"] if use_thresholds else 0
        seats = self.system["adjustment_threshold_seats"] if use_thresholds else 0

        self.desired_col_sums, self.adj_seat_gen, _, _ \
            = apportion1d_general(
                v_votes = self.nat_votes,
                num_total_seats = self.total_const_seats + nat_seats,
                prior_allocations = self.results["fixed_grand_total"],
                rule = self.system.get_generator("adj_determine_divider"),
                type_of_rule = self.system.get_type("adj_determine_divider"),
                threshold_percent = threshold,
                threshold_choice = choice,
                threshold_seats = seats
            )


        self.ref_seat_alloc, _, _, _ \
            = apportion1d_general(
                v_votes = self.nat_votes,
                num_total_seats = self.total_const_seats + nat_seats,
                prior_allocations = [0]*len(self.nat_votes),
                rule = self.system.get_generator('adj_determine_divider'),
                type_of_rule = self.system.get_type('adj_determine_divider')
                )

    def set_forced_reasons(self, demoTable):
        if "Criteria" in demoTable["headers"]:
            criteria_idx = demoTable["headers"].index("Criteria")
            for row in demoTable["steps"]:
                (constituency, party) = row[1:3]
                const = [c["name"] for c in self.system["constituencies"]]
                parties = self.system["parties"]
                constIdx = const.index(constituency)
                partyIdx = parties.index(party)
                if self.votes[constIdx,partyIdx] < 1:
                    row[criteria_idx] = "Forced allocation"
        return demoTable

    def run_adjustment_apportionment(self):
        """Conduct adjustment seat apportionment."""
        method = ADJUSTMENT_METHODS[self.system["adjustment_method"]]
        self.gen = self.system.get_generator("adj_alloc_divider")
        consts = self.system["constituencies"]
        fixed_seats = [con["num_fixed_seats"] for con in consts]
        (all_const_seats, stepbystep) = method (
            self.votes,
            self.desired_row_sums,
            self.desired_col_sums,
            np.array(self.results["fixed_const_seats"]),
            self.gen,
            # kwargs-arguments:
            adj_seat_gen = self.adj_seat_gen, # both icelandic_xxx
            v_fixed_seats = fixed_seats, # used by norwegian_law
            last = self.last, # used by nearest_to_previous
            nat_prior_allocations = (self.results['fixed_nat_seats']
                                     if self.party_vote_info['specified']
                                     else None),
        )
        adj_const_seats = subtract_m(all_const_seats, self.results["fixed_const_seats"])
        self.results["all_const_seats"] = all_const_seats
        self.results["adj_const_seats"] = adj_const_seats
        self.results["adj_const_total"] = [sum(x) for x in zip(*adj_const_seats)]
        self.results["all_const_total"] = [sum(x) for x in zip(*all_const_seats)]

        alloc_sequence = stepbystep["data"]
        self.demo_tables = []
        format = DEMO_TABLE_FORMATS[self.system["adjustment_method"]]
        functions = [stepbystep["function"]]
        if "additional_function" in stepbystep:
            functions.append(stepbystep["additional_function"])
        else:
            format = [format]            
        for i, print_demo_table in enumerate(functions):
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

    def calculate_ref_seat_shares(self, scaling):
        import numpy as np, numpy.linalg as la, math as m
        nrows = self.num_constituencies()
        ncols = self.num_parties()
        col_sums = np.array(self.desired_col_sums)
        row_sums = np.array(self.desired_row_sums)
        ref_seat_shares = np.copy(self.votes).astype(float)
        row_constraints = scaling in {"both", "const"}
        col_constraints = scaling in {"both", "party"}
        if ncols > 1 and nrows > 1:
            iter = 0
            if row_constraints and col_constraints:
                while True:
                    iter+=1
                    # overall step
                    delta = sum(sum(x) for x in ref_seat_shares) / sum(row_sums)
                    ref_seat_shares /= delta
                    # exit condition
                    if m.isclose(sum(abs(sum(ref_seat_shares[c, :])-row_sums[c])
                                     for c in range(nrows)), 0.0, abs_tol=1e-7) and \
                        m.isclose(sum(max(sum(ref_seat_shares[:, p])-col_sums[p], 0.0)
                                      for p in range(ncols)), 0.0, abs_tol=1e-7):
                        break
                    # constituency step
                    for c in range(nrows):
                        row_sum = row_sums[c]
                        s = sum(ref_seat_shares[c, :])
                        eta = s/row_sum if row_sum > 0 else 0
                        if eta == 0:
                            ref_seat_shares[c, :] *= 0
                        else:
                            ref_seat_shares[c, :] /= eta
                    # party step
                    for p in range(ncols):
                        col_sum = col_sums[p]
                        s = sum(ref_seat_shares[:, p])
                        tau = max(s/col_sum, 1) if col_sum > 0 else 0
                        if tau == 0:
                            ref_seat_shares[:, p] *= tau
                        else:
                            ref_seat_shares[:, p] /= tau
                print(iter) #TODO: remove this iter if it all works and program doesn't get stuck fro too long in loop
            elif row_constraints:
                for c in range(nrows):
                    row_sum = row_sums[c]
                    s = sum(ref_seat_shares[c, :])
                    eta = row_sum / s if s > 0 else 1
                    ref_seat_shares[c, :] *= eta
            elif col_constraints:
                for p in range(ncols):
                    col_sum = col_sums[p]
                    s = sum(ref_seat_shares[:, p])
                    tau = col_sum / s if s > 0 else 1
                    ref_seat_shares[:, p] *= tau
        self.ref_seat_shares = ref_seat_shares
        self.total_ref_seat_shares = self.ref_seat_shares.sum(0)
        if self.party_vote_info['specified']:
            self.total_ref_nat = self.desired_col_sums - self.total_ref_seat_shares
        else:
            self.total_ref_seat_shares = self.ref_seat_shares.sum(0)

    def calculate_ref_seat_shares_old(self, scaling):
        import numpy as np, numpy.linalg as la
        nrows = self.num_constituencies()
        ncols = self.num_parties()
        col_sums = np.array(self.desired_col_sums)
        row_sums = np.array(self.desired_row_sums)
        if self.party_vote_info['specified'] and scaling in {"const", "party","total"}:
            scalar = sum(col_sums) / (sum(sum(x) for x in self.votes) +
                                      sum(self.party_votes))
            matrix = np.vstack(self.votes, self.party_votes)
            ref_seat_shares = matrix*scalar
            if scaling == 'const':
                nrows += 1
                row_sums = np.append(row_sums, sum(col_sums) -
                                     self.total_const_seats)
        else:
            scalar = float(self.total_const_seats)/sum(sum(x) for x in self.votes)
            ref_seat_shares = self.votes * scalar
        error = 1
        row_constraints = scaling in {"both", "const"}
        col_constraints = scaling in {"both", "party"}
        if ncols > 1 and nrows > 1:
            if row_constraints and col_constraints:
                p_null_seats = []
                for p in range(ncols):
                    if col_sums[p] == 0:
                        p_null_seats.append(p)
                        ref_seat_shares[:, p] *= 0
                while round(error, 7) != 0.0:
                    error = 0
                    #constituency step
                    for c in range(nrows):
                        row_sum = row_sums[c]
                        s = sum(ref_seat_shares[c,:])
                        eta = row_sum/s if s > 0 else 1
                        ref_seat_shares[c, :] *= eta
                        error = max(error, abs(1 - eta))
                    if all(round(i, 7) >= 1 for i in [col_sums[p]/(ref_seat_shares.sum(0)[p] \
                            if ref_seat_shares.sum(0)[p] > 0 else 1) for p in range(ncols)]):
                        break
                    #party step
                    p_at_lim = p_null_seats.copy()
                    p_under_lim = np.setdiff1d(np.arange(ncols), p_at_lim).tolist()
                    gammas = np.array([col_sums[p]/ref_seat_shares.sum(axis=0)[p] for p in p_under_lim])
                    gamma = np.amin(gammas)
                    error = max(error, abs(1 - gamma))
                    p_gamma = p_under_lim[np.argmin(gammas)]
                    ref_seat_shares *= gamma
                    p_at_lim.append(p_gamma)
                    p_under_lim.remove(p_gamma)
                    nparty_at_lim = len(p_at_lim)
                    for i in range(ncols-nparty_at_lim):
                        gammas = np.array([col_sums[p]/ref_seat_shares.sum(axis=0)[p] for p in p_under_lim])
                        gamma = np.amin(gammas)
                        p_gamma = p_under_lim[np.argmin(gammas)]
                        sum_shares = sum([ref_seat_shares.sum(axis=0)[p]*gamma for p in p_under_lim]) +\
                                     sum([ref_seat_shares.sum(axis=0)[p] for p in p_at_lim])
                        if sum_shares > self.total_const_seats:
                            break
                        for p in p_under_lim:
                            ref_seat_shares[:,p] *= gamma
                        p_at_lim.append(p_gamma)
                        p_under_lim.remove(p_gamma)
                        error = max(error, abs(1 - gamma))
                    if len(p_under_lim):
                        gamma = (self.total_const_seats - sum([ref_seat_shares.sum(axis=0)[p] for p in p_at_lim]))\
                                /sum([ref_seat_shares.sum(axis=0)[p] for p in p_under_lim])
                        for p in p_under_lim:
                            ref_seat_shares[:, p] *= gamma
                        error = max(error, abs(1 - gamma))
            elif row_constraints:
                for c in range(nrows):
                    row_sum = row_sums[c]
                    s = sum(ref_seat_shares[c, :])
                    eta = row_sum/s if s > 0 else 1
                    ref_seat_shares[c, :] *= eta
            elif col_constraints:
                for p in range(ncols):
                    col_sum = col_sums[p]
                    s = sum(ref_seat_shares[:, p])
                    tau = col_sum/s if s > 0 else 1
                    ref_seat_shares[:, p] *= tau

        self.ref_seat_shares = ref_seat_shares
        if self.party_vote_info['specified']:
            if row_constraints and col_constraints:
                self.total_ref_seat_shares = self.ref_seat_shares.sum(0)
                self.total_ref_nat = self.desired_col_sums - self.total_ref_seat_shares
            else:
                self.total_ref_nat = self.ref_seat_shares[-1]
                self.ref_seat_shares = self.ref_seat_shares[:-1]
                self.total_ref_seat_shares = self.ref_seat_shares.sum(0)
        else:
            self.total_ref_seat_shares = self.ref_seat_shares.sum(0)
