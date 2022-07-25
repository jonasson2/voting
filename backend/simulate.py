# import logging
from datetime import datetime
from measure_groups import MeasureGroups, function_dict
import dictionaries as dicts
import random
from voting import Election
from dictionaries import LIST_MEASURES, VOTE_MEASURES, CONSTANTS, SENS_MEASURES
from dictionaries import STATISTICS_HEADINGS, EXCEL_HEADINGS
from electionHandler import ElectionHandler
from generate_votes import generate_votes
from running_stats import Running_stats
#from system import System
from table_util import add_totals, find_xtd_shares, m_subtract, find_bias
from util import hms, shape
from copy import deepcopy, copy
from util import disp, dispv, remove_prefix, sum_abs_diff
from histogram import Histogram
from sim_measures import add_vuedata
# logging.basicConfig(filename='logs/simulate.log', filemode='w',
# format='%(name)s - %(levelname)s - %(message)s')

class Collect(dict):
    # collect values into dictionaries of arrays
    def add(self, key, x):
        if key in self:
            self[key].append(x)
        else:
            self[key] = [x]

class SimulationSettings(dict):
    def __init__(self):
        self["simulate"] = False
        self["simulation_count"] = 200
        self["cpu_count"] = CONSTANTS['default_cpu_count']
        self["gen_method"] = "gamma"
        self["distribution_parameter"] = CONSTANTS["CoeffVar"]
        self["scaling"] = "both"
        self["selected_rand_constit"] = "All constituencies"
        self["sensitivity"] = False

    def abs(q, s):      return abs(q - s)
    def sq(q, s):       return (q - s)**2


class Simulation():
    # Simulate a set of elections in a single thread
    def __init__(self, sim_settings, systems, vote_table, nr=0):
        warnings_to_errors()
        self.min_votes = CONSTANTS["minimum_votes"]
        election_handler = ElectionHandler(vote_table, systems, self.min_votes)
        self.election_handler = election_handler
        self.measure_groups = MeasureGroups(systems, nr)
        self.base_allocations = []
        self.systems = [election.system
                        for election in election_handler.elections]
        self.nsys = len(self.systems)
        for (election, sys) in zip(election_handler.elections, self.systems):
            sys.reference_results = deepcopy(election.results)
        self.parties = vote_table["parties"]
        self.sim_settings = sim_settings
        self.sim_count = self.sim_settings["simulation_count"]
        self.distribution = self.sim_settings["gen_method"]
        self.var_coeff = self.sim_settings["distribution_parameter"]
        self.iterations_with_no_solution = 0
        self.terminate = False
        # ------- Following properties are only used by excel_util.py
        self.constituencies = self.systems[0]["constituencies"]
        self.vote_table = vote_table
        self.num_parties = len(self.parties)
        self.num_constituencies = len(self.constituencies)
        self.sensitivity = sim_settings["sensitivity"]
        self.apply_random = self.index_of_const_to_apply_randomness_to()
        # --------
        self.iteration = 0
        self.total_time = 0
        self.time_left = 0
        self.initialize_stat_counters()
        self.run_initial_elections()

    def initialize_stat_counters(self):
        ns = self.nsys
        nclist = [len(sys["constituencies"]) for sys in self.systems]
        np = len(self.parties)
        self.MEASURES = self.measure_groups.get_all_measures()
        parallel = self.sim_settings["cpu_count"] > 1
        self.STAT_LIST = list(STATISTICS_HEADINGS.keys())
        self.MEASURE_LIST = list(EXCEL_HEADINGS.keys())
        self.stat = {}
        for measure in VOTE_MEASURES:
            self.stat[measure] = [None]*ns
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i] = Running_stats((nc + 1, np + 1), parallel)
        for measure in LIST_MEASURES:
            self.stat[measure] = [None]*ns
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i] = Running_stats((nc + 1, np + 1), parallel)
        for measure in SENS_MEASURES:
            self.stat[measure] = [None]*ns
            for i in range(ns):
                self.stat[measure][i] = Histogram()
        for measure in self.MEASURES:  # Was MEASURES in earlier version
            self.stat[measure] = Running_stats(ns, parallel)
        for cmp_system in self.systems:
            if cmp_system["compare_with"]:
                measure = "cmp_" + cmp_system["name"]
                self.stat[measure] = Running_stats(ns, parallel)
                self.stat[measure + "_tot"] = Running_stats(ns, parallel)

    def run_initial_elections(self):
        for election in self.election_handler.elections:
            xtd_total_seats = add_totals(election.results)
            xtd_fixed_seats = add_totals(election.m_fixed_seats)
            xtd_adj_seats = m_subtract(xtd_total_seats, xtd_fixed_seats)
            xtd_seat_shares = find_xtd_shares(xtd_total_seats)
            election.calculate_ideal_seats(self.sim_settings["scaling"])
            xtd_ideal_seats = add_totals(election.ideal_seats)
            self.base_allocations.append({
                "xtd_fixed_seats": xtd_fixed_seats,
                "xtd_adj_seats":   xtd_adj_seats,
                "xtd_total_seats": xtd_total_seats,
                "xtd_seat_shares": xtd_seat_shares,
                "xtd_ideal_seats": xtd_ideal_seats,
            })

    def simulate(self, tasknr=0, monitor=None):
        # Simulate many elections.
        if self.sim_count == 0:
            return
        gen = self.gen_votes()
        self.iterations_with_no_solution = 0
        begin_time = datetime.now()
        for i in range(self.sim_count):
            self.iteration = i + 1
            votes = next(gen)
            self.run_and_collect_measures(votes)  # This allocates
            round_end = datetime.now()
            elapsed = (round_end - begin_time).total_seconds()
            time_pr_iter = elapsed/(i + 1)
            self.time_left = hms(time_pr_iter*(self.sim_count - i))
            self.total_time = hms(elapsed)
            if monitor:
                self.terminate = monitor.monitor(tasknr, self.iteration)
            if self.terminate:
                break
        return

    def gen_votes(self):
        # Generate votes similar to given votes using selected distribution
        while True:
            votes = generate_votes(
                self.election_handler.votes, self.var_coeff,
                self.distribution, self.apply_random)
            yield votes

    def collect_votes(self, votes):
        for (i,election) in enumerate(self.election_handler.elections):
            xtd_votes = add_totals(election.m_votes)
            xtd_shares = find_xtd_shares(xtd_votes)
            self.stat["sim_votes"][i].update(xtd_votes)
            self.stat["sim_shares"][i].update(xtd_shares)

    def collect_list_measures(self):
        import numpy as np
        for (i,election) in enumerate(self.election_handler.elections):
            cs = np.array(add_totals(election.m_fixed_seats))
            ts = np.array(add_totals(election.results))
            election.calculate_ideal_seats(self.sim_settings["scaling"])
            ids = np.array(add_totals(election.ideal_seats))
            adj = ts - cs  # this computes the adjustment seats
            sh = ts/np.maximum(1, ts[:, -1, None])  # divide by last column
            self.stat["fixed_seats"][i].update(cs)
            self.stat["total_seats"][i].update(ts)
            self.stat["adj_seats"][i].update(adj)
            self.stat["seat_shares"][i].update(sh)
            self.stat["ideal_seats"][i].update(ids)

    def run_and_collect_measures(self, votes):
        # allocate seats according to votes:
        #print("it", self.iteration)
        self.election_handler.run_elections(votes, threshold=False) # A
        if self.sensitivity:
            self.run_sensitivity(votes)
        else:
            self.collect_votes(votes)
            self.collect_list_measures()
            self.collect_general_measures()

    def collect_general_measures(self):
        deviations = Collect()
        elections = self.election_handler.elections
        for (system, election) in zip(self.systems, elections):
            self.add_deviation(election, "dev_ref", system.reference_results,
                               deviations)
            deviations.add("entropy", election.entropy())
            for (cmp_election, cmp_system) in zip(elections, self.systems):
                if cmp_system["compare_with"]:
                    cmp_results = cmp_election.results
                    measure = "cmp_" + cmp_system["name"]
                    self.add_deviation(election, measure, cmp_results,
                                       deviations)
            self.deviation_measures(election, system, deviations)
            self.other_measures(election, deviations)
        for m in deviations.keys():
            if m in self.stat:
                self.stat[m].update(deviations[m])

    def deviation_measures(self, election, system, deviations):
        for measure in ["dev_all_adj", "dev_all_fixed", "one_const"]:
            option = remove_prefix(measure, "dev_")
            comparison_system = system.generate_system(option)
            comparison_election = Election(comparison_system,
                                           election.m_votes, self.min_votes)
            comparison_results = comparison_election.run()
            self.add_deviation(election, measure, comparison_results,
                               deviations)

    @staticmethod
    def add_deviation(election, measure, comparison_results, deviations):
        deviation = sum_abs_diff(election.results, comparison_results)
        if deviation:
            deviations.add(measure, deviation)
        else:
            deviations.add(measure, 0)
        totals = [sum(x) for x in zip(*election.results)]
        comparison_totals = [sum(x) for x in zip(*comparison_results)]
        deviation = sum_abs_diff([totals], [comparison_totals])
        deviations.add(measure + "_tot", deviation)

    def sum_func(self, election, function):
        measure = sum([
            function(election.ideal_seats[c][p], election.results[c][p])
            for p in range(len(self.parties))
            for c in range(election.num_constituencies())
            if self.vote_table['votes'][c][p] >= 1
        ])
        return measure

    def other_measures(self, election, deviations):
        #ideal_seats = self.calculate_ideal_seats(election)
        for (funcname, function) in function_dict.items():
            measure = "sum_" + funcname ### KJ. bæta við að sleppa listum með atkvæði sem eru núll
            deviations.add(measure, self.sum_func(election, function))
        # deviations.add("sum_abs", self.sum_abs(election))
        # deviations.add("sum_pos", self.sum_pos(election))
        # deviations.add("sum_sq", self.sum_sq(election))
        (slope, corr) = self.bias(election)
        deviations.add("min_seat_val", self.min_seat_val(election))
        deviations.add("bias_slope", slope)
        deviations.add("bias_corr", corr)

    def run_sensitivity(self, votes):
        elections = self.election_handler.elections
        variation_coefficient = self.sim_settings["sens_cv"]
        sens_method = self.sim_settings["sens_method"]
        sens_votes = generate_votes(votes, variation_coefficient, sens_method)
        for (i, (election, system)) in enumerate(zip(elections, self.systems)):
            sens_election = Election(system, sens_votes, self.min_votes)
            sens_election.run()
            party_seats1 = election.v_desired_col_sums
            party_seats2 = sens_election.v_desired_col_sums
            party_seat_diff = sum_abs_diff(party_seats1, party_seats2)
            if party_seat_diff > 0:
                self.stat["party_sens"][i].update(party_seat_diff)
            else:
                list_seats1 = election.results
                list_seats2 = sens_election.results
                list_seat_diff = sum_abs_diff(list_seats1, list_seats2)
                self.stat["list_sens"][i].update(list_seat_diff)

    def bias(self, election):
        (slope,corr) = find_bias(election.results, election.ideal_seats)
        return slope,corr

    # Loosemore-Hanby
    def sum_abs(self, election):
        lh = sum([
            abs(election.ideal_seats[c][p] - election.results[c][p])
            for p in range(len(self.parties))
            for c in range(election.num_constituencies())
        ])
        return lh

    # Minimized by Sainte Lague
    def sum_sq(self, election):
        ids = election.ideal_seats
        stl = sum([
            (ids[c][p] - election.results[c][p])**2/ids[c][p]
            for p in range(len(self.parties))
            for c in range(election.num_constituencies())
            if ids[c][p] != 0
        ])
        return stl

    # Maximized by d'Hondt
    def min_seat_val(self, election):
        ids = election.ideal_seats
        dh_min = min([
            ids[c][p]/float(election.results[c][p])
            for p in range(len(self.parties))
            for c in range(election.num_constituencies())
            if election.results[c][p] != 0
        ])
        return dh_min

    # Minimized by d'Hondt
    def sum_pos(self, election):
        ids = election.ideal_seats
        dh_sum = sum([
            max(0, ids[c][p] - election.results[c][p])/ids[c][p]
            for p in range(len(self.parties))
            for c in range(election.num_constituencies())
            if ids[c][p] != 0
        ])
        return dh_sum

    def index_of_const_to_apply_randomness_to(self):
        sel_rand = self.sim_settings["selected_rand_constit"]
        cons = [c["name"] for c in self.constituencies]
        if sel_rand not in cons or sel_rand == "All constituencies":
            index = -1
        else:
            index = cons.index(sel_rand)
        return index

    def attributes(self):
        dictionary = copy(vars(self))
        del dictionary["election_handler"]
        stat = dictionary['stat']
        for (key,val) in stat.items():
            if isinstance(val, list):
                for i in range(len(val)):
                    val[i] = vars(val[i]) if val[i] else {}
            else:
                stat[key] = vars(stat[key])
        return dictionary

    # def get_raw_result(self):
    #     # Used to transfer simulation results to Sim_result object
    #     # Must be a dictionary to make it through multiprocessing interface
    #     result = {}
    #     result["apply_random"] = self.apply_random
    #     result["base_allocations"] = self.base_allocations
    #     result["constituencies"] = self.constituencies
    #     result["iteration"] = self.iteration
    #     result["MEASURES"] = self.measure_groups.get_all_measures()
    #     result["parties"] = self.parties
    #     result["sim_settings"] = self.sim_settings
    #     result["stat"] = self.stat
    #     result["STAT_LIST"] = self.STAT_LIST
    #     result["systems"] = self.systems
    #     result["total_time"] = self.total_time
    #     result["var_coef"] = self.var_coef
    #     result["vote_table"] = self.vote_table
    #     result["xtd_vote_shares"] = self.xtd_vote_shares
    #     result["xtd_votes"] = self.xtd_votes
    #     #disp('result', result)
    #     return result

class Sim_result:
    # Results from one simulation, or several combined simulations
    def __init__(self, dictionary):
        warnings_to_errors()
        for (key,val) in dictionary.items():
            if key=='stat':
                for statkey, statval in val.items():
                    if isinstance(statval,list):
                        for i in range(len(statval)):
                            if statkey.endswith('sens'):
                                statval[i] = Histogram(statval[i])
                            else:
                                statval[i] = Running_stats.from_dict(statval[i])
                    else:
                        if statkey.endswith('sens'):
                            val[statkey] = Histogram(statval[i])
                        else:
                            val[statkey] = Running_stats.from_dict(statval)
            setattr(self, key, val)

        # self.data = [{} for _ in range(self.nsys)]
        # self.list_data = [{} for _ in range(self.nsys + 1)]
        # self.vote_data = [{} for _ in range(self.nsys)]

    def combine(self, sim_result):
        self.iteration += sim_result.iteration
        self.total_time += sim_result.total_time
        nclist = [len(sys["constituencies"]) for sys in self.systems]
        for measure in VOTE_MEASURES:
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in LIST_MEASURES:
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in SENS_MEASURES:
            for i in range(len(self.systems)):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in self.MEASURES:  # Was MEASURES in earlier version
            self.stat[measure].combine(sim_result.stat[measure])
        for cmp_system in self.systems:
            if cmp_system["compare_with"]:
                measure = "cmp_" + cmp_system["name"]
                self.stat[measure].combine(sim_result.stat[measure])
                self.stat[measure + "_tot"].combine(sim_result.stat[measure + "_tot"])

    def analyze_general(self):
        for m in self.MEASURES:
            dd = self.find_datadict(self.stat[m], self.MEASURE_LIST)
            for i in range(self.nsys):
                self.data[i][m] = dict((s, dd[s][i]) for s in self.MEASURE_LIST)

    def analyze_vote_data(self):
        for m in VOTE_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                self.vote_data[i][m] = dict((s, dd[s]) for s in self.STAT_LIST)

    def analyze_list_data(self):
        for m in LIST_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                D = {}
                for s in self.STAT_LIST:
                    D[s] = dd[s]
                self.list_data[i][m] = D

    def analysis(self):
        # Calculate averages and variances of various quality measures.
        self.data = [{} for _ in range(self.nsys)]
        self.list_data = [{} for _ in range(self.nsys + 1)]
        self.vote_data = [{} for _ in range(self.nsys)]
        if hasattr(self, 'sensitivity') and self.sensitivity:
            self.list_sensitivity = self.gethistograms("list")
            self.party_sensitivity = self.gethistograms("party")
        else:
            self.analyze_general()
            self.analyze_list_data()
            self.analyze_vote_data()
            self.list_data[-1] = self.vote_data[0]  # used by excel_util
        # Það er villa sem á eftir að leiðrétta þegar búið er að "mergja" Excel
        # útskrift (des. 2021). Vote-data er bara skrifað út fyrir fyrsta kerfið
        # í list_data[-1] en ef sum kerfin eru með sameinuð kjördæmi (í "All")
        # þá getur vote-datað orðið misjafnt milli kerfa; excel_util.py ræður
        # bara við að skrifa eitt vote_data.

    def find_datadict(self, statentry, stat_list):
        from math import sqrt
        stat_function = {
            "avg": statentry.mean,
            "std": statentry.std,
            "lo95": statentry.lo95ci,
            "hi95": statentry.hi95ci,
            "skw": statentry.skewness,
            "kur": statentry.kurtosis,
            "min": statentry.minimum,
            "max": statentry.maximum
        }
        datadict = {}
        nsim = self.iteration
        for stat in stat_list:
            datadict[stat] = stat_function[stat]()
        return datadict

    def gethistograms(self, type):
        # Get list of histograms, one for each system, divide keys by 2
        stat = self.stat[type + "_sens"] # histogram for each system
        counts = []
        for s in stat:
            count = {}
            for (k, v) in s.get().items():
                assert k % 2 == 0
                count[k//2] = v
            counts.append(count)
        return counts

    def get_result_dict(self, parallel):
        result_dict = {
            "iteration":        self.iteration,
            "systems":          self.systems,
            "parties":          self.parties,
            "sim_settings":     self.sim_settings,
            "testnames":        [systems["name"]
                                 for systems in self.systems],
            "methods":          [systems["adjustment_method"]
                                for systems in self.systems],
            "vote_data":        self.vote_data,
            "vote_table":       self.vote_table,
            "base_allocations": self.base_allocations,
            "data":         [{
                "name":           self.systems[sysnr]["name"],
                "method":         self.systems[sysnr]["adjustment_method"],
                "measures":       self.data[sysnr],
                "list_measures":  self.list_data[sysnr]
            }
                for sysnr in range(len(self.systems))
            ]
        }
        add_vuedata(result_dict, parallel)
        return result_dict

def warnings_to_errors():
    # Catch NumPy warnings (e.g. zero divide):
    import warnings
    warnings.filterwarnings('error', category=RuntimeWarning)
    warnings.filterwarnings('error', category=UserWarning)
