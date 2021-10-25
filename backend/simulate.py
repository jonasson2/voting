# from voting import Election, SIMULATION_VARIATES
import logging
import json
from datetime import datetime, timedelta
from math import sqrt, exp
from copy import copy, deepcopy

from table_util import m_subtract, scale_matrix, add_totals, find_xtd_shares
from excel_util import simulation_to_xlsx
from rules import Rules
import dictionaries as dicts
from dictionaries import MEASURES, LIST_MEASURES, VOTE_MEASURES, AGGREGATES
from generate_votes import generate_votes, generate_maxchange_votes
import voting
from electionHandler import ElectionHandler
from running_stats import Running_stats

def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=200, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

logging.basicConfig(filename='logs/simulate.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def hms(sec):
    sec = round(sec)
    min = sec // 60; sec %= 60
    hr = min // 60;  min %= 60
    d = hr // 24; hr %= 24
    s = f"{min:02}:{sec:02}"
    if hr > 0: s = f"{hr:02}" + s
    if d == 1: s = "1 day + " + s
    elif d > 1: s = f"{d} days + " + s
    return s

def dev(results, ref):
    """Calculate seat deviation of results compared to reference results."""
    assert(len(results) == len(ref))
    d = 0
    for c in range(len(results)):
        assert(len(results[c]) == len(ref[c]))
        for p in range(len(results[c])):
            d += abs(results[c][p] - ref[c][p])
    return d

def votes_to_change(election):
    """
    Find how many additional votes each individual list must receive
    for the results of the given election to change.
    """
    ref_results = election.results
    ref_votes = election.m_votes
    votes_to_change = []
    votes = deepcopy(ref_votes)
    for c in range(len(ref_results)):
        votes_to_change.append([])
        for p in range(len(ref_results[c])):
            if ref_votes[c][p] == 0:
                votes_to_change[c].append(None)
                continue
            a = 0
            b = int(0.1*votes[c][p])
            d = 0
            while d == 0:
                votes[c][p] = ref_votes[c][p]+b
                election = voting.Election(election.rules, votes)
                results = election.run()
                d = dev(results, ref_results)
                if d == 0:
                    a = copy(b)
                    b = int(sqrt(2)*b)
            m = b-a
            x = 0
            while m > 1:
                x = int(m*sqrt(0.5) + a)
                votes[c][p] = ref_votes[c][p]+x
                election = voting.Election(election.rules, votes)
                results = election.run()
                d = dev(results, ref_results)
                if d == 0:
                    a = copy(x)
                else:
                    b = copy(x)
                m = b-a
            votes_to_change[c].append(b)
            votes[c][p] = ref_votes[c][p]

    return votes_to_change

class SimulationRules(Rules):
    def __init__(self):
        super(SimulationRules, self).__init__()
        # Simulation rules
        self.value_rules = {
            #Fair share constraints:
            "row_constraints": {True, False},
            "col_constraints": {True, False},
        }
        self["simulate"] = False
        self["simulation_count"] = 100
        self["gen_method"] = "beta"
        self["distribution_parameter"] = 0.25
        self["scaling"] = "both"
        self["selected_rand_constit"] = "All"
        # self["row_constraints"] = True
        # self["col_constraints"] = True

class Simulation:
    """Simulate a set of elections."""
    def __init__(self, sim_rules, e_rules, vote_table):
        self.e_handler = ElectionHandler(vote_table, e_rules)
        self.e_rules = [el.rules for el in self.e_handler.elections]
        self.num_rulesets = len(self.e_rules)
        self.vote_table = self.e_handler.vote_table
        self.constituencies = self.vote_table["constituencies"]
        self.num_constituencies = len(self.constituencies)
        self.parties = self.vote_table["parties"]
        self.num_parties = len(self.parties)
        self.base_votes = self.vote_table["votes"]
        self.xtd_votes = add_totals(self.base_votes)
        self.xtd_vote_shares = find_xtd_shares(self.xtd_votes)
        self.sim_rules = sim_rules
        self.num_total_simulations = self.sim_rules["simulation_count"]
        self.variate = self.sim_rules["gen_method"]
        self.var_coeff = self.sim_rules["distribution_parameter"]
        self.iteration = 0
        self.terminate = False
        self.total_time = timedelta(0)
        self.time_left = 0
        self.iterations_with_no_solution = 0
        self.reference = []
        sel_rand_const = sim_rules["selected_rand_constit"]
        if sel_rand_const == "All":
            self.apply_random = -1
        else:
            constit = [c["name"] for c in self.constituencies]
            assert sel_rand_const in constit
            self.apply_random = constit.index(sel_rand_const)
        self.stat = {}
        self.data = []
        self.list_data = []
        self.vote_data = {}
        nr = self.num_rulesets
        nc = self.num_constituencies
        np = self.num_parties
        for measure in VOTE_MEASURES:
            self.stat[measure] = Running_stats((nc+1,np+1))
        for measure in MEASURES:
            self.stat[measure] = Running_stats(nr)
        for measure in LIST_MEASURES:
            self.stat[measure] = Running_stats((nr,nc+1,np+1))
        for ruleset in range(self.num_rulesets):
            self.reference.append([])
        self.run_initial_elections()
        self.find_reference()

    def analyze(self, measures, type_of_data):
        is_vote_data = type_of_data == "vote"
        datadict = {}
        stat_list = ["avg", "std", "skw", "kur", "min", "max"]
        for measure in measures:
            datadict[measure] = {}
            datadict[measure]["avg"] = self.stat[measure].mean()
            datadict[measure]["std"] = self.stat[measure].std()
            datadict[measure]["skw"] = self.stat[measure].skewness()
            datadict[measure]["kur"] = self.stat[measure].kurtosis()
            datadict[measure]["min"] = self.stat[measure].minimum()
            datadict[measure]["max"] = self.stat[measure].maximum()
        if is_vote_data:
            for m in measures:
                self.vote_data[m] = dict((s, datadict[m][s]) for s in stat_list)
        else:
            for r in range(self.num_rulesets):
                self.list_data.append({})
                self.data.append({})
                for m in measures:
                    ddm = datadict[m]
                    if type_of_data == "list":
                        self.list_data[r][m] = dict((s, ddm[s][r]) for s in stat_list)
                    else:
                        self.data[r][m] = dict((s, ddm[s][r]) for s in stat_list)

    def run_initial_elections(self):
        self.base_allocations = []
        for election in self.e_handler.elections:
            xtd_total_seats = add_totals(election.results)
            xtd_const_seats = add_totals(election.m_const_seats_alloc)
            xtd_adj_seats = m_subtract(xtd_total_seats, xtd_const_seats)
            xtd_seat_shares = find_xtd_shares(xtd_total_seats)
            ideal_seats = self.calculate_ideal_seats(election)
            xtd_ideal_seats = add_totals(ideal_seats)
            self.base_allocations.append({
                "xtd_const_seats": xtd_const_seats,
                "xtd_adj_seats": xtd_adj_seats,
                "xtd_total_seats": xtd_total_seats,
                "xtd_seat_shares": xtd_seat_shares,
                "xtd_ideal_seats": xtd_ideal_seats,
                "step_info": election.adj_seats_info,
            })

    def gen_votes(self):
        """
        Generate votes similar to given votes using selected distribution
        """
        while True:
            if self.variate == "maxchange":
                votes = generate_maxchange_votes(
                    self.base_votes, self.var_coeff, self.apply_random)
            else:
                votes = generate_votes(
                    self.base_votes, self.var_coeff, self.variate,
                    self.apply_random)
            yield votes

    def collect_votes(self, votes):
        xtd_votes  = add_totals(votes)
        xtd_shares = find_xtd_shares(xtd_votes)
        self.stat["sim_votes"].update(xtd_votes)
        self.stat["sim_shares"].update(xtd_shares)

    def find_reference(self):
        self.e_handler.set_votes(self.base_votes)
        for ruleset in range(self.num_rulesets):
            election = self.e_handler.elections[ruleset]
            self.reference[ruleset] = election.results
            #self.reference[ruleset] = election.results

    def collect_measures(self, votes):
        # votes are simulated; this function allocates seats
        self.e_handler.set_votes(votes)
        self.collect_votes(votes)
        self.collect_list_measures()
        self.collect_general_measures()

    # def collect_list_measures(self, ruleset, election):
    def collect_list_measures(self):
        import numpy as np
        cs = []
        ts = []
        ids = []
        for ruleset in range(self.num_rulesets):
            election = self.e_handler.elections[ruleset]                     
            cs.append(add_totals(election.m_const_seats_alloc))
            ts.append(add_totals(election.results))
            ids.append(add_totals(self.calculate_ideal_seats(election)))
        cs = np.array(cs)
        ts = np.array(ts)
        ids = np.array(ids)
        adj = ts - cs
        sh = ts/np.maximum(1, ts[:,-1,None]) # divide by last column
        self.stat["const_seats"].update(cs)
        self.stat["total_seats"].update(ts)
        self.stat["adj_seats"].update(adj)
        self.stat["seat_shares"].update(sh)
        self.stat["ideal_seats"].update(ids)

    # def collect_general_measures(self, ruleset, election):
    def collect_general_measures(self):
        """Various tests to determine the quality of the given method."""
        measure_list = ["adj_dev", "entropy", "entropy_ratio",
                        "sum_abs", "sum_pos", "sum_sq", "min_seat_value"]
        deviation_list = ["dev_opt", "dev_law", "dev_all_adj",
                          "dev_all_const", "dev_ref"]
        deviation_list.extend([d + "_totals" for d in deviation_list])
        self.measures = dict((m,[]) for m in measure_list)
        self.deviations = dict((m,[]) for m in deviation_list)
        for ruleset in range(self.num_rulesets):
            election = self.e_handler.elections[ruleset]
            self.measures["adj_dev"].append(election.adj_dev)
            opt_results = self.opt_results_and_entropy(election)
            self.deviation_measures(ruleset, election, opt_results)
            self.other_measures(ruleset, election)
        for measure in measure_list:
            self.stat[measure].update(self.measures[measure])
        for measure in deviation_list:
            self.stat[measure].update(self.deviations[measure])

    def opt_results_and_entropy(self, election):
        opt_rules = election.rules.generate_opt_ruleset()
        opt_election = voting.Election(opt_rules, election.m_votes)
        opt_results = opt_election.run()
        entropy = election.entropy()
        entropy_ratio = exp(entropy - opt_election.entropy())
        self.measures["entropy"].append(entropy)
        self.measures["entropy_ratio"].append(entropy_ratio)
        return opt_results

    def deviation_measures(self, ruleset, election, opt_results):
        self.deviation(ruleset, "opt",       election, opt_results)
        self.deviation(ruleset, "law",       election)
        self.deviation(ruleset, "all_adj",   election)
        self.deviation(ruleset, "all_const", election)
        self.deviation(ruleset, "ref",       election, self.reference[ruleset])

    def other_measures(self, ruleset, election):
        ideal_seats = self.calculate_ideal_seats(election)
        self.sum_abs(ruleset, election, ideal_seats)
        self.sum_pos(ruleset, election, ideal_seats)
        self.sum_sq(ruleset, election, ideal_seats)
        self.min_seat_value(ruleset, election, ideal_seats)

    def deviation(self, ruleset, option, election,
                  comparison_results = None):
        votes = election.m_votes
        results = election.results
        if comparison_results == None:
            rules = self.e_rules[ruleset].generate_comparison_rules(option)
            comparison_results = voting.Election(rules, votes).run()
        deviation = dev(results, comparison_results)
        measure = "dev_" + option
        self.deviations[measure].append(deviation)
        ref_totals = [sum(x) for x in zip(*results)]
        comp_totals = [sum(x) for x in zip(*comparison_results)]
        deviation = dev([ref_totals], [comp_totals])
        measure = "dev_" + option + "_totals"
        self.deviations[measure].append(deviation)

    def calculate_ideal_seats(self, election):
        scalar = float(election.total_seats) / sum(sum(x) for x in election.m_votes)
        ideal_seats = scale_matrix(election.m_votes, scalar)
        assert election.solvable
        rein = 0
        error = 1
        if self.num_parties > 1 and election.num_constituencies > 1:
            row_constraints = self.sim_rules["scaling"] in {"both","const"}
            col_constraints = self.sim_rules["scaling"] in {"both","party"}
            while round(error, 5) != 0.0:
                error = 0
                if row_constraints:
                    for c in range(election.num_constituencies):
                        s = sum(ideal_seats[c])
                        if s != 0:
                            mult = float(election.v_desired_row_sums[c])/s
                            error += abs(1-mult)
                            mult += rein*(1-mult)
                            for p in range(self.num_parties):
                                ideal_seats[c][p] *= mult
                if col_constraints:
                    for p in range(self.num_parties):
                        s = sum([c[p] for c in ideal_seats])
                        if s != 0:
                            mult = float(election.v_desired_col_sums[p])/s
                            error += abs(1-mult)
                            mult += rein*(1-mult)
                            for c in range(election.num_constituencies):
                                ideal_seats[c][p] *= mult

        try:
            assert [sum(x) for x in zip(*ideal_seats)] == election.v_desired_col_sums
            assert [sum(x) for x in ideal_seats] == election.v_desired_row_sums
        except AssertionError:
            pass

        return ideal_seats

    #Loosemore-Hanby
    def sum_abs(self, ruleset, election, ideal_seats):
        lh = sum([
            abs(ideal_seats[c][p]-election.results[c][p])
            for p in range(self.num_parties)
            for c in range(election.num_constituencies)
        ])
        self.measures["sum_abs"].append(lh)

    #Minimized by Sainte Lague
    def sum_sq(self, ruleset, election, ideal_seats):
        stl = sum([
            (ideal_seats[c][p]-election.results[c][p])**2/ideal_seats[c][p]
            for p in range(self.num_parties)
            for c in range(election.num_constituencies)
            if ideal_seats[c][p] != 0
        ])
        self.measures["sum_sq"].append(stl)

    #Maximized by d'Hondt
    def min_seat_value(self, ruleset, election, ideal_seats):
        dh_min = min([
            ideal_seats[c][p]/float(election.results[c][p])
            for p in range(self.num_parties)
            for c in range(election.num_constituencies)
            if election.results[c][p] != 0
        ])
        self.measures["min_seat_value"].append(dh_min)

    #Minimized by d'Hondt
    def sum_pos(self, ruleset, election, ideal_seats):
        dh_sum = sum([
            max(0, ideal_seats[c][p]-election.results[c][p])/ideal_seats[c][p]
            for p in range(self.num_parties)
            for c in range(election.num_constituencies)
            if ideal_seats[c][p] != 0
        ])
        self.measures["sum_pos"].append(dh_sum)        

    def analysis(self):
        """Calculate averages and variances of various quality measures."""
        self.analyze(MEASURES, "data")
        self.analyze(LIST_MEASURES, "list")
        self.analyze(VOTE_MEASURES, "vote")
        
    def simulate(self):
        """Simulate many elections."""
        gen = self.gen_votes()
        ntot = self.num_total_simulations;
        if ntot == 0:
            self.collect_measures(self.base_votes)
        self.iterations_with_no_solution = 0
        begin_time = datetime.now()
        for i in range(ntot):
            if self.terminate and i > 0:
                break
            self.iteration = i + 1
            votes = next(gen)
            try:
                self.collect_measures(votes)
            except ValueError:
                self.iterations_with_no_solution += 1
                continue
            round_end = datetime.now()
            elapsed = (round_end - begin_time).total_seconds()
            time_pr_iter = elapsed/(i+1)
            self.time_left = hms(time_pr_iter*(ntot - i))
            self.total_time = hms(elapsed)
        self.analysis()
        self.list_data.append({})
        self.list_data[-1] = self.vote_data
        # self.test_generated() --- needs to be rewritten,
        # (statistical test of simulated data)

    def get_results_dict(self):
        #self.analysis()
        return {
            "e_rules": self.e_rules,
            "parties": self.parties,
            "testnames": [rules["name"] for rules in self.e_rules],
            "methods": [rules["adjustment_method"] for rules in self.e_rules],
            "measures": MEASURES,
            "list_deviation_measures": dicts.LIST_DEVIATION_MEASURES,
            "totals_deviation_measures": dicts.TOTALS_DEVIATION_MEASURES,
            "ideal_comparison_measures": dicts.IDEAL_COMPARISON_MEASURES,
            "standardized_measures": dicts.STANDARDIZED_MEASURES,
            "list_measures": dicts.LIST_MEASURES,
            "vote_measures": dicts.VOTE_MEASURES,
            "aggregates": dicts.AGGREGATES,
            "data": [{
                "name": self.e_rules[ruleset]["name"],
                "method": self.e_rules[ruleset]["adjustment_method"],
                "measures": self.data[ruleset],
                "list_measures": self.list_data[ruleset]
              }
              for ruleset in range(self.num_rulesets)
            ],
            "vote_data": self.vote_data
        }

    def to_xlsx(self, filename):
        simulation_to_xlsx(self, filename)
