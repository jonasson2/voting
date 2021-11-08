# import logging
from datetime import datetime
from measure_groups import MeasureGroups
import dictionaries as dicts
import voting
from dictionaries import LIST_MEASURES, MEASURES, VOTE_MEASURES
from electionHandler import ElectionHandler
from excel_util import simulation_to_xlsx
from generate_votes import generate_maxchange_votes, generate_votes
from running_stats import Running_stats
from systems import Systems
from table_util import add_totals, find_xtd_shares, m_subtract, scale_matrix
from util import hms


def disp(title, value, depth=99):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(compact=False, width=100, depth=depth).pprint
    print("\n" + title.upper() + ":")
    pp(value)

# logging.basicConfig(filename='logs/simulate.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def dev(results, ref):  # Compute sum of absolute values of ref minus results
    if len(results) != len(ref):
        x = 1
    assert (len(results) == len(ref))
    d = 0
    for c in range(len(results)):
        assert (len(results[c]) == len(ref[c]))
        for p in range(len(results[c])):
            d += abs(results[c][p] - ref[c][p])
    return d

class Collect(dict):
    # collect values into dictionaries of arrays
    def add(self, key, x):
        if key in self:
            self[key].append(x)
        else:
            self[key] = [x]

class SimulationSettings(Systems):
    def __init__(self):
        super(SimulationSettings, self).__init__()
        # Simulation systems
        self.value_rules = {
            # Fair share constraints:
            "row_constraints": {True, False},
            "col_constraints": {True, False},
        }
        self["simulate"] = False
        self["simulation_count"] = 100
        self["gen_method"] = "beta"
        self["distribution_parameter"] = 0.25
        self["scaling"] = "both"
        self["selected_rand_constit"] = "All constituencies"
        # self["row_constraints"] = True
        # self["col_constraints"] = True

class Simulation:
    # Simulate a set of elections.
    def __init__(self, sim_settings, systems, vote_table):
        self.measure_groups = MeasureGroups(systems)
        self.base_allocations = []
        self.election_handler = ElectionHandler(vote_table, systems)
        #                                  (computes reference results)
        self.elections = self.election_handler.elections
        # The systems from elections have correct constituencies:
        self.systems = [el.system for el in self.elections]
        self.parties = vote_table["parties"]
        self.base_votes = vote_table["votes"]
        self.xtd_votes = add_totals(self.base_votes)
        self.xtd_vote_shares = find_xtd_shares(self.xtd_votes)
        self.sim_settings = sim_settings
        self.sim_count = self.sim_settings["simulation_count"]
        self.variate = self.sim_settings["gen_method"]
        self.var_coeff = self.sim_settings["distribution_parameter"]
        self.iteration = 0
        self.terminate = False
        self.total_time = 0
        self.time_left = 0
        self.iterations_with_no_solution = 0
        self.reference = [[] for _ in range(len(self.systems))]
        # ---- Following properties are only used by excel_util.py
        self.constituencies = self.systems[0]["constituencies"]
        self.vote_table = vote_table
        self.num_parties = len(self.parties)
        self.num_constituencies = len(self.constituencies)
        # --------
        sel_rand = sim_settings["selected_rand_constit"]
        cons = [c["name"] for c in self.constituencies]
        if sel_rand not in cons or sel_rand == "All constituencies":
            self.apply_random = -1
        else:
            self.apply_random = cons.index(sel_rand)
        self.stat = {}
        self.data = [{} for _ in range(len(self.systems))]
        self.list_data = [{} for _ in range(len(self.systems) + 1)]
        self.vote_data = {}
        nr = self.num_systems
        nc = self.num_constituencies
        np = self.num_parties
        self.measures = self.measure_groups.get_all_measures()
        for measure in VOTE_MEASURES:
            self.stat[measure] = Running_stats((nc + 1, np + 1))
        for measure in LIST_MEASURES:
            self.stat[measure] = Running_stats((nr,nc+1,np+1))
        for measure in MEASURES:
            self.stat[measure] = Running_stats(nr)
        print("Running run_initial_elections")
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
                self.vote_data[m] = dict((stat, datadict[m][stat])
                                         for stat in stat_list)
        else:
            for sys in range(len(self.systems)):
                for m in measures:
                    ddm = datadict[m]
                    if type_of_data == "list":
                        self.list_data[sys][m] = dict((stat, ddm[stat][sys])
                                                      for stat in stat_list)
                    else:
                        # disp("dd", datadict["dev_ref"])
                        self.data[sys][m] = dict((stat, ddm[stat][sys])
                                                 for stat in stat_list)
        # disp("sd", self.data[0])

    def run_initial_elections(self):
        for election in self.elections:
            xtd_total_seats = add_totals(election.results)
            xtd_const_seats = add_totals(election.m_const_seats_alloc)
            xtd_adj_seats = m_subtract(xtd_total_seats, xtd_const_seats)
            xtd_seat_shares = find_xtd_shares(xtd_total_seats)
            ideal_seats = self.calculate_ideal_seats(election)
            xtd_ideal_seats = add_totals(ideal_seats)
            self.base_allocations.append({
                "xtd_const_seats": xtd_const_seats,
                "xtd_adj_seats":   xtd_adj_seats,
                "xtd_total_seats": xtd_total_seats,
                "xtd_seat_shares": xtd_seat_shares,
                "xtd_ideal_seats": xtd_ideal_seats,
                "step_info":       election.adj_seats_info,
            })

    def gen_votes(self):
        # Generate votes similar to given votes using selected distribution
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
        xtd_votes = add_totals(votes)
        xtd_shares = find_xtd_shares(xtd_votes)
        self.stat["sim_votes"].update(xtd_votes)
        self.stat["sim_shares"].update(xtd_shares)

    def find_reference(self):
        self.election_handler.set_votes(self.base_votes)
        for election in self.elections:
            election.set_reference_results()

    def collect_list_measures(self):
        import numpy as np
        cs = []
        ts = []
        ids = []
        for sysnr in range(len(self.systems)):
            election = self.elections[sysnr]
            cs.append(add_totals(election.m_const_seats_alloc))
            ts.append(add_totals(election.results))
            ids.append(add_totals(self.calculate_ideal_seats(election)))
        cs = np.array(cs)
        ts = np.array(ts)
        ids = np.array(ids)
        adj = ts - cs  # this computes the adjustment seats
        sh = ts/np.maximum(1, ts[:, -1, None])  # divide by last column
        self.stat["const_seats"].update(cs)
        self.stat["total_seats"].update(ts)
        self.stat["adj_seats"].update(adj)
        self.stat["seat_shares"].update(sh)
        self.stat["ideal_seats"].update(ids)

    def collect_measures(self, votes):
        # votes are simulated; this function allocates seats
        self.election_handler.set_votes(votes)
        self.collect_votes(votes)
        self.collect_list_measures()
        self.collect_general_measures()

    def collect_general_measures(self):
        deviations = Collect()
        for (election, system) in zip(self.elections, self.systems):
            deviations.add("entropy", election.entropy())
            for (cmp_election, cmp_system) in zip(self.elections, self.systems):
                if cmp_system["compare_with"]:
                    cmp_results = cmp_election.results
                    measure = "cmp_" + cmp_system["name"]
                    self.add_deviation(election, measure, cmp_results, deviations)
            self.deviation_measures(election, system, deviations)
            self.other_measures(election, deviations)
        for m in deviations.keys():
            self.stat[m].update(deviations[m])

    def deviation_measures(self, election, system, deviations):
        for measure in ["dev_all_adj", "dev_all_const", "one_const"]:
            option = measure.removeprefix("dev_")
            comparison_system = system.generate_comparison_rules(option)
            comparison_results = voting.Election(comparison_system, election.m_votes).run()
            self.add_deviation(election, measure, comparison_results, deviations)

    @staticmethod
    def add_deviation(election, measure, comparison_results, deviations):
        if measure != "one_const":
            deviation = dev(election.results, comparison_results)
            deviations.add(measure, deviation)
        totals = [sum(x) for x in zip(*election.results)]
        comparison_totals = [sum(x) for x in zip(*comparison_results)]
        deviation = dev([totals], [comparison_totals])
        deviations.add(measure + "_tot", deviation)

    def other_measures(self, election, deviations):
        ideal_seats = self.calculate_ideal_seats(election)
        deviations.add("sum_abs", self.sum_abs(election, ideal_seats))
        deviations.add("sum_pos", self.sum_pos(election, ideal_seats))
        deviations.add("sum_sq", self.sum_sq(election, ideal_seats))
        deviations.add("min_seat_val", self.min_seat_val(election, ideal_seats))

    def calculate_ideal_seats(self, election):
        scalar = float(election.total_seats)/sum(sum(x) for x in election.m_votes)
        ideal_seats = scale_matrix(election.m_votes, scalar)
        assert election.solvable
        rein = 0
        error = 1
        if len(self.parties) > 1 and election.num_constituencies > 1:
            row_constraints = self.sim_settings["scaling"] in {"both", "const"}
            col_constraints = self.sim_settings["scaling"] in {"both", "party"}
            while round(error, 5) != 0.0:
                error = 0
                if row_constraints:
                    for c in range(election.num_constituencies):
                        s = sum(ideal_seats[c])
                        if s != 0:
                            mult = float(election.v_desired_row_sums[c])/s
                            error += abs(1 - mult)
                            mult += rein*(1 - mult)
                            for p in range(len(self.parties)):
                                ideal_seats[c][p] *= mult
                if col_constraints:
                    for p in range(len(self.parties)):
                        s = sum([c[p] for c in ideal_seats])
                        if s != 0:
                            mult = float(election.v_desired_col_sums[p])/s
                            error += abs(1 - mult)
                            mult += rein*(1 - mult)
                            for c in range(election.num_constituencies):
                                ideal_seats[c][p] *= mult

        try:
            assert [sum(x) for x in zip(*ideal_seats)] == election.v_desired_col_sums
            assert [sum(x) for x in ideal_seats] == election.v_desired_row_sums
        except AssertionError:
            pass

        return ideal_seats

    # Loosemore-Hanby
    def sum_abs(self, election, ideal_seats):
        lh = sum([
            abs(ideal_seats[c][p] - election.results[c][p])
            for p in range(len(self.parties))
            for c in range(election.num_constituencies)
        ])
        return lh

    # Minimized by Sainte Lague
    def sum_sq(self, election, ideal_seats):
        stl = sum([
            (ideal_seats[c][p] - election.results[c][p])**2/ideal_seats[c][p]
            for p in range(len(self.parties))
            for c in range(election.num_constituencies)
            if ideal_seats[c][p] != 0
        ])
        return stl

    # Maximized by d'Hondt
    def min_seat_val(self, election, ideal_seats):
        dh_min = min([
            ideal_seats[c][p]/float(election.results[c][p])
            for p in range(len(self.parties))
            for c in range(election.num_constituencies)
            if election.results[c][p] != 0
        ])
        return dh_min

    # Minimized by d'Hondt
    def sum_pos(self, election, ideal_seats):
        dh_sum = sum([
            max(0, ideal_seats[c][p] - election.results[c][p])/ideal_seats[c][p]
            for p in range(len(self.parties))
            for c in range(election.num_constituencies)
            if ideal_seats[c][p] != 0
        ])
        return dh_sum

    def analysis(self):
        # Calculate averages and variances of various quality measures.
        self.analyze(MEASURES, "data")
        self.analyze(LIST_MEASURES, "list")
        self.analyze(VOTE_MEASURES, "vote")
        self.list_data[-1] = self.vote_data  # used by excel_util

    def simulate(self):
        # Simulate many elections.
        gen = self.gen_votes()
        ntot = self.sim_count
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
                self.collect_measures(votes)  # This allocates seats
            except ValueError:
                self.iterations_with_no_solution += 1
                continue
            round_end = datetime.now()
            elapsed = (round_end - begin_time).total_seconds()
            time_pr_iter = elapsed/(i + 1)
            self.time_left = hms(time_pr_iter*(ntot - i))
            self.total_time = hms(elapsed)
        self.analysis()
        # self.test_generated() --- needs to be rewritten,
        # (statistical test of simulated data)

    def get_results_dict(self):
        self.analysis()
        return {
            "systems":                   self.systems,
            "parties":                   self.parties,
            "testnames":                 [systems["name"] for systems in self.systems],
            "methods":                   [systems["adjustment_method"] for systems in self.systems],
            "measures":                  MEASURES,
            "list_deviation_measures":   dicts.LIST_DEVIATION_MEASURES,
            "totals_deviation_measures": dicts.TOTALS_DEVIATION_MEASURES,
            "ideal_comparison_measures": dicts.IDEAL_COMPARISON_MEASURES,
            "standardized_measures":     dicts.STANDARDIZED_MEASURES,
            "list_measures":             dicts.LIST_MEASURES,
            "vote_measures":             dicts.VOTE_MEASURES,
            "aggregates":                dicts.AGGREGATES,
            "data":                      [{
                "name":          self.systems[sysnr]["name"],
                "method":        self.systems[sysnr]["adjustment_method"],
                "measures":      self.data[sysnr],
                "list_measures": self.list_data[sysnr]
            }
                for sysnr in range(len(self.systems))
            ],
            "vote_data":                 self.vote_data
        }

    def to_xlsx(self, filename):
        simulation_to_xlsx(self, filename)
