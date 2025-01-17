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

    def __init__(self, system, votes, party_vote_info=None, vote_table_name=''):
        if party_vote_info is None:
            party_vote_info = {'name':'-', 'num_fixed_seats':0, 'num_adj_seats':0,
                               'votes':[],'specified':False, 'total':0}
        self.nconst = len(system["constituencies"])
        self.nparty = len(system["parties"])
        self.system = system
        self.party_vote_info = party_vote_info
        self.party_votes = np.array(party_vote_info["votes"])
        self.set_votes(votes)
        self.reference_results = []
        self.vote_table_name = vote_table_name
        self.stored_entropy = None

    def entropy(self):
        if self.stored_entropy is None:
            self.stored_entropy = entropy(self.votes, self.results['all_const_seats'],
                                          self.gen)
        return self.stored_entropy

    def set_reference_results(self):
        self.reference_results = self.results['all_const_seats']

    def set_votes(self, votes, party_votes=None):
        # votesums: column sums of m_votes
        self.votes = np.array(votes)
        if party_votes:
            self.party_votes = np.array(party_votes)
        if self.nconst == 1:
            self.votes = self.votes.sum(0)[None,:]
        else:
            assert len(self.votes) == self.nconst
        assert all(len(row) == self.nparty for row in self.votes)
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

        for k,v in results.items():
            results[k] = v.tolist()

        all = results["all_const_seats"] + [results["all_const_total"]]
        fix = results["fixed_const_seats"] + [results["fixed_const_total"]]
        adj = results["adj_const_seats"] + [results["adj_const_total"]]

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

        self.results["ref_seat_alloc"] = self.ref_seat_alloc.tolist()
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

    def assign_seats(self, use_thresholds=True):
        self.fixed_seats_alloc = []
        self.order = []
        self.desired_row_sums = np.array([
            const["num_fixed_seats"] + const["num_adj_seats"]
            for const in self.system["constituencies"]
        ])
        party_vote_info = self.party_vote_info
        self.total_const_seats = sum(self.desired_row_sums)
        self.apportion_fixed_seats(use_thresholds)
        self.apportion_total_party_seats(use_thresholds)
        self.allocate_adjustment_seats()
        if party_vote_info["specified"]:
            self.add_national_adjustment_seats()
        else:
            self.results['all_grand_total'] = self.results['all_const_total']
        self.prepare_results()
        pass

    def voteless_seats(self):
        over = [None]*self.nconst
        all_const_seats = self.results["all_const_seats"]
        for c in range(self.nconst):
            for p in range(self.nparty):
                over[c] = [r > 0 and float(v) == 0
                           for (r, v) in zip(all_const_seats[c], self.votes[c])]
        return over

    def any_voteless(self):
        return any(v for x in self.voteless_seats() for v in x)

    def apportion_fixed_seats(self, use_thresholds):
        constituencies = self.system["constituencies"]
        threshold = self.system["constituency_threshold"] if use_thresholds else 0
        m_allocations = np.zeros((self.nconst, self.nparty), int)
        self.last = []
        self.results = {}
        for i in range(self.nconst):
            num_seats = constituencies[i]["num_fixed_seats"]
            if num_seats != 0:
                alloc, _, last_in = apportion1d_general(
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
                alloc = np.zeros(self.nparty, int)
                self.last.append({'idx': None, 'active_votes': 0})
            m_allocations[i,:] = alloc

        v_allocations = m_allocations.sum(0)
        self.results["fixed_const_total"] = v_allocations

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
                nat_fixed_alloc, _, _ = apportion1d_general(
                    v_votes = self.nat_votes,
                    num_total_seats = self.system["nat_seats"]["num_fixed_seats"],
                    prior_allocations = [],
                    rule = self.system.get_generator("primary_divider"),
                    type_of_rule = self.system.get_type("primary_divider"),
                    threshold_percent = threshold
                )
                v_allocations += nat_fixed_alloc
            else:
                nat_fixed_alloc = np.zeros(len(self.party_votes), int)
            self.results["fixed_nat_seats"] = nat_fixed_alloc
            
        self.results["fixed_const_seats"] = m_allocations
        self.results["fixed_grand_total"] = v_allocations

    def apportion_total_party_seats(self, use_thresholds):
        """Calculate the number of adjustment seats each party gets."""
        nat_seats = ((self.system["nat_seats"]['num_fixed_seats'] +
                      self.system["nat_seats"]['num_adj_seats']) \
                         if self.party_vote_info['specified'] else 0)

        threshold = self.system["adjustment_threshold"] if use_thresholds else 0
        choice = self.system["adj_threshold_choice"] if use_thresholds else 0
        seats = self.system["adjustment_threshold_seats"] if use_thresholds else 0

        self.desired_col_sums, self.adj_seat_gen, _ \
            = apportion1d_general(
                v_votes = self.nat_votes,
                num_total_seats = self.total_const_seats + nat_seats,
                prior_allocations = np.array(self.results["fixed_grand_total"]),
                rule = self.system.get_generator("adj_determine_divider"),
                type_of_rule = self.system.get_type("adj_determine_divider"),
                threshold_percent = threshold,
                threshold_choice = choice,
                threshold_seats = seats
            )

        self.ref_seat_alloc, _, _ \
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

    def allocate_adjustment_seats(self):
        """Conduct adjustment seat apportionment."""
        method = ADJUSTMENT_METHODS[self.system["adjustment_method"]]
        self.gen = self.system.get_generator("adj_alloc_divider")
        consts = self.system["constituencies"]
        fixed_seats = [con["num_fixed_seats"] for con in consts]
        (all_const_seats, stepbystep) = method(
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
        adj_const_seats = all_const_seats - self.results["fixed_const_seats"]
        self.results["all_const_seats"] = all_const_seats
        self.results["adj_const_seats"] = adj_const_seats
        self.results["adj_const_total"] = adj_const_seats.sum(0)
        self.results["all_const_total"] = all_const_seats.sum(0)

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
        self.results["adj_nat_seats"] = (self.desired_col_sums
                                         - self.results["fixed_grand_total"]
                                         - self.results["adj_const_total"])
        self.results["all_nat_seats"] = (self.results["fixed_nat_seats"]
                                         + self.results["adj_nat_seats"])
        self.results["adj_grand_total"] = (self.results["adj_const_total"]
                                           +self.results["adj_nat_seats"])
        self.results["all_grand_total"] = (self.results["fixed_grand_total"]
                                           + self.results["adj_grand_total"])

    def fix_special_formats(self):
        for table in self.demo_tables:
            fmtlist = list(table['format'])
            for j, f in enumerate(fmtlist):
                if f == 's' and any(table['steps']):
                    maxw = max(len(s[j]) for s in table['steps'])
                    fmtlist[j] = "c"  if maxw <= 2 else "l"
            table['format'] = "".join(fmtlist)


    def calculate_ref_seat_shares(self, scaling, id=None):
        import numpy as np, numpy.linalg as la, math as m
        nrows = self.nconst
        ncols = self.nparty
        col_sums = np.array(self.desired_col_sums)
        row_sums = np.array(self.desired_row_sums)
        ref_seat_shares = np.copy(self.votes).astype(float)*self.total_const_seats/sum(self.votesums)
        row_constraints = scaling in {"both", "const"}
        col_constraints = scaling in {"both", "party"}
        error = 1e-8
        if ncols > 1 and nrows > 1:
            iter = 0
            if row_constraints and col_constraints:
                '''
                if sum(col_sums) != sum(row_sums): # förum í einfaldari gerð ef það eru jöfnur TODO: laga
                    error = 1
                    while round(error, 7) != 0.0:
                        error = 0
                        for c in range(nrows):
                            row_sum = self.desired_row_sums[c]
                            s = sum(ref_seat_shares[c, :])
                            eta = row_sum / s if s > 0 else 1
                            ref_seat_shares[c, :] *= eta
                            error = max(error, abs(1 - eta))
                        for p in range(ncols):
                            col_sum = col_sums[p]
                            s = sum(ref_seat_shares[:, p])
                            tau = col_sum / s if s > 0 else 1
                            ref_seat_shares[:, p] *= tau
                            error = max(error, abs(1 - tau))
                else:
                '''
                while True:
                    iter+=1
                    # constituency step
                    for c in range(nrows):
                        s = sum(ref_seat_shares[c, :])
                        eta = s/row_sums[c] if row_sums[c] > 0 else 0
                        if eta == 0:
                            ref_seat_shares[c, :] *= 0
                        else:
                            ref_seat_shares[c, :] /= eta
                    # party step
                    iii = 0
                    over = list(filter(lambda p: sum(ref_seat_shares[:, p]) > col_sums[p] + error, range(ncols)))
                    while over:
                        iii +=1
                        H = list(filter(lambda p:
                                        sum(ref_seat_shares[:, p]) >= col_sums[p] + error,
                                        range(ncols)))
                        not_H = list(set(range(ncols)) - set(H))
                        for p in H:
                            s = sum(ref_seat_shares[:, p])
                            tau = s / col_sums[p] if col_sums[p] > 0 else 0
                            if tau == 0:
                                ref_seat_shares[:, p] *= 0
                            else:
                                ref_seat_shares[:, p] /= tau
                        if not_H:
                            s = sum(sum(ref_seat_shares[:, p]) for p in not_H)
                            tau = s/(self.total_const_seats-sum(col_sums[p] for p in H))
                            for p in not_H:
                                if tau == 0:
                                    ref_seat_shares[:, p] *= 0
                                else:
                                    ref_seat_shares[:, p] /= tau
                        over = list(filter(lambda p: sum(ref_seat_shares[:, p]) > col_sums[p] + error, range(ncols)))
                # exit condition
                    if np.all([m.isclose(abs(sum(ref_seat_shares[c, :]) - row_sums[c]), 0.0, abs_tol=error)
                                     for c in range(nrows)]):
                            #and m.isclose(sum(max(sum(ref_seat_shares[:, p])-col_sums[p], 0.0)
                            #          for p in range(ncols)), 0.0, abs_tol=1e-8):
                        break
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
