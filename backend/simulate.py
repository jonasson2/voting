# import logging
from datetime import datetime
from measure_groups import MeasureGroups, function_dict, function_dict_party
import dictionaries as dicts
import random
from voting import Election
from dictionaries import SEAT_MEASURES, VOTE_MEASURES, CONSTANTS, SENS_MEASURES
from dictionaries import HISTOGRAM_MEASURES, PARTY_MEASURES
from dictionaries import STATISTICS_HEADINGS, EXCEL_HEADINGS
from electionHandler import ElectionHandler
from generate_votes import generate_votes
from running_stats import Running_stats
#from system import System
from table_util import add_totals, find_percentages, m_subtract, find_bias, add_total
from util import hms, shape, average
from copy import deepcopy, copy
from util import disp, dispv, remove_prefix, sum_abs_diff
from histogram import Histogram
from sim_measures import add_vuedata
import numpy as np
# logging.basicConfig(filename='logs/simulate.log', filemode='w',
# format='%(name)s - %(levelname)s - %(message)s')

class Collect(dict):
    # collect values into dictionaries of arrays
    def add(self, key, x):
        if not x:
            x = 0
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
        self["const_cov"] = CONSTANTS["CoeffVar"]
        self["party_vote_cov"] = CONSTANTS["CoeffVar"]/2
        self["use_thresholds"] = False
        self["scaling"] = "both"
        self["selected_rand_constit"] = "All constituencies"
        self["sensitivity"] = False

    def abs(q, s):      return abs(q - s)
    def sq(q, s):       return (q - s)**2


class Simulation():
    # Simulate a set of elections in a single thread
    def __init__(self, sim_settings, systems, vote_table, nr=0):
        warnings_to_errors()
        use_thresholds = sim_settings['use_thresholds']
        self.sim_settings = sim_settings
        self.vote_table = vote_table
        self.reference_handler = ElectionHandler(vote_table, systems, use_thresholds)
        self.election_handler = ElectionHandler(vote_table, systems, use_thresholds)
        self.systems = [election.system for election in self.election_handler.elections]
        self.party_votes_specified = self.vote_table["party_vote_info"]["specified"]
        self.measure_groups = MeasureGroups(systems, self.party_votes_specified, nr)
        self.base_allocations = []
        self.parties = vote_table["parties"]
        self.sim_count = sim_settings["simulation_count"]
        self.distribution = sim_settings["gen_method"]
        self.const_cov = sim_settings["const_cov"]
        self.party_vote_cov = sim_settings["party_vote_cov"]
        self.terminate = False
        # ------- Following properties are only used by excel_util.py
        self.constituencies = [c['name'] for c in vote_table["constituencies"]]
        self.nsys = len(self.reference_handler.elections)
        self.nparty = len(self.parties)
        self.nconst = len(self.constituencies)
        self.sensitivity = sim_settings["sensitivity"]
        self.apply_random = self.index_of_const_to_apply_randomness_to()
        # -------- Following is used for plotting
        #self.disparity_data = [pd.DataFrame(columns=self.parties) for sys in range(self.nsys)]
        # --------
        self.iteration = 0
        self.total_time = 0
        self.time_left = 0
        self.initialize_stat_counters()
        self.run_initial_elections()

    def initialize_stat_counters(self):
        ns = self.nsys
        np = self.nparty
        nclist = [len(sys["constituencies"]) for sys in self.systems]
        self.MEASURES = self.measure_groups.get_all_measures(self.party_votes_specified)
        parallel = self.sim_settings["cpu_count"] > 1
        self.STAT_LIST = list(STATISTICS_HEADINGS.keys())
        self.MEASURE_LIST = list(EXCEL_HEADINGS.keys())
        self.stat = {}
        n1 = 2 if self.party_votes_specified else 1
        n2 = 3 if self.party_votes_specified else 1
        for measure in VOTE_MEASURES:
            self.stat[measure] = [None]*ns
            for (i,nc) in enumerate(nclist):
                nrow = nc + 1 if measure in {"neg_margin","neg_margin_count"} else nc + n1
                self.stat[measure][i] = Running_stats((nrow, np+1), parallel, measure)
        for measure in SEAT_MEASURES:
            self.stat[measure] = [None]*ns
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i] = Running_stats((nc + n2, np+1), parallel, measure)
        for measure in SENS_MEASURES:
            self.stat[measure] = [None]*ns
            for i in range(ns):
                self.stat[measure][i] = Histogram()
        for measure in self.MEASURES:
            self.stat[measure] = Running_stats(ns, parallel, measure)
        extensions = ['const', 'tot']
        for measure in HISTOGRAM_MEASURES:
            self.stat[measure] = [None]*ns*np
            for i in range(ns*np):
                self.stat[measure][i] = Histogram()
        for measure in PARTY_MEASURES:
            self.stat[measure] = [None] * ns
            for s in range(ns):
                #store = measure=='party_disparity'
                self.stat[measure][s] = Running_stats(np, parallel, measure)
        if self.party_votes_specified:
            extensions.extend(['nat', 'grand'])
        for cmp_system in self.systems:
            if cmp_system["compare_with"]:
                for extension in extensions:
                    measure = "cmp_" + cmp_system["name"] + "_" + extension
                    self.stat[measure] = Running_stats(ns, parallel, measure)

    def run_initial_elections(self):
        #total_overhang = sum(sum(x) for x in overhang)
        for i,election in enumerate(self.reference_handler.elections):
            election.calculate_ref_seat_shares(self.sim_settings["scaling"])
            disparity, excess, shortage = self.calculate_party_disparity(election)
            party_overhang = self.calculate_potential_overhang(election)
            ids = add_totals(election.ref_seat_shares)
            neg_margins, neg_parties = self.calculate_negative_margins(election)
            const_party_margins, cpm_counts = self.neg_margin_matrix(neg_margins, neg_parties)
            if self.party_votes_specified:
                ids.append(add_total(election.total_ref_nat))
                ids.append([x+y for (x,y) in zip(ids[-2], ids[-1])])
            self.base_allocations.append({
                "fixed_seats": election.results["fix"],
                "adj_seats":   election.results["adj"],
                "total_seats": election.results["all"],
                "total_seat_percentages": find_percentages(election.results["all"]),
                "ref_seat_shares": ids,
                "ref_seat_alloc": election.ref_seat_alloc,
                "party_disparity": disparity,
                "party_excess": excess,
                "party_shortage": shortage,
                "party_overhang": party_overhang,
                "neg_margins": const_party_margins,
                "neg_margin_count": cpm_counts
            })
            #self.disparity_data[i].loc[len(self.disparity_data[i])] = disparity

    def simulate(self, tasknr=0, monitor=None):
        # Simulate many elections.
        if self.sim_count == 0:
            return
        gen = self.gen_votes()
        begin_time = datetime.now()
        for i in range(self.sim_count):
            self.iteration = i + 1
            print(f'iteration = {self.iteration}')
            (votes, party_votes) = next(gen)
            self.run_and_collect_measures(votes, party_votes)  # This allocates
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
                self.election_handler.votes, self.const_cov,
                self.distribution, self.apply_random)
            if self.party_votes_specified:
                party_votes = generate_votes(
                    [self.election_handler.party_vote_info["votes"]], self.party_vote_cov,
                    self.distribution, self.apply_random)
                yield (votes, party_votes[0])
            else:
                yield (votes, None)

    def run_and_collect_measures(self, votes, party_votes):
        use_thresholds = self.sim_settings["use_thresholds"]
        self.election_handler.run_elections(use_thresholds, votes, party_votes)
        if self.sensitivity:
            self.run_sensitivity(votes)
        else:
            self.collect_vote_measures()
            self.collect_seat_measures()
            self.collect_party_measures()
            self.collect_general_measures()

    def collect_vote_measures(self):
        for (i,election) in enumerate(self.election_handler.elections):
            votes = np.array(add_totals(election.m_votes))
            if self.party_votes_specified:
                votes = np.vstack((votes, add_total(election.nat_votes)))
            vote_percentages = find_percentages(votes)
            #const_party_disparity = self.calculate_const_party_disparity(election)
            #self.stat["neg_margin"][i].update()
            self.stat["sim_votes"][i].update(votes)
            self.stat["sim_vote_percentages"][i].update(vote_percentages)

    def collect_seat_measures(self):
        for (i,election) in enumerate(self.election_handler.elections):
            cs = np.array(election.results["fix"])
            ts = np.array(election.results["all"])
            election.calculate_ref_seat_shares(self.sim_settings["scaling"])
            ids = np.array(add_totals(election.ref_seat_shares))
            if self.party_votes_specified:
                ids = np.vstack((ids, add_total(election.total_ref_nat)))
                ids = np.vstack((ids, ids[-2,:] + ids[-1,:]))
            adj = ts - cs  # this computes the adjustment seats
            sh = ts/np.maximum(1, ts[:, -1, None])  # divide by last column
            self.stat["total_seat_percentages"][i].update(sh)
            self.stat["fixed_seats"][i].update(cs)
            self.stat["adj_seats"][i].update(adj)
            self.stat["total_seats"][i].update(ts)
            self.stat["ref_seat_shares"][i].update(ids)

    def collect_party_measures(self):
        for (i, election) in enumerate(self.election_handler.elections):
            nat_vote_percentages = [x / sum(election.nat_votes) for x in election.nat_votes]
            disparity, excess, shortage = self.calculate_party_disparity(election)
            party_overhang = self.calculate_potential_overhang(election)
            self.stat["nat_vote_percentages"][i].update(nat_vote_percentages)
            self.stat["party_ref_seat_shares"][i].update(election.total_ref_seat_shares)
            self.stat["party_total_seats"][i].update(election.results["all_grand_total"])
            self.stat["ref_seat_alloc"][i].update(election.ref_seat_alloc)
            self.stat["party_disparity"][i].update(disparity)
            self.stat["party_excess"][i].update(excess)
            self.stat["party_shortage"][i].update(shortage)
            self.stat["party_overhang"][i].update(party_overhang)
            for p in range(self.nparty):
                self.stat["disparity_count"][i*self.nparty + p].update(disparity[p])
                self.stat["overhang_count"][i*self.nparty + p].update(party_overhang[p])

    def collect_general_measures(self):
        deviations = Collect()
        ref_elections = self.reference_handler.elections
        elections = self.election_handler.elections
        for i, (ref_election, election) in enumerate(zip(ref_elections, elections)):
            system = election.system
            self.add_deviation(election, ref_election, "dev_ref", deviations)
            neg_margins, neg_parties = self.calculate_negative_margins(election)
            const_party_margins, cpm_counts = self.neg_margin_matrix(neg_margins, neg_parties)
            self.stat["neg_margin"][i].update(const_party_margins)
            self.stat["neg_margin_count"][i].update(cpm_counts)
            deviations.add("max_neg_margin", max(neg_margins))
            deviations.add("avg_neg_margin", average(neg_margins))
            deviations.add("entropy", election.entropy())
            excess, shortage, disparity = self.calculate_disparity(election)
            deviations.add("excess", excess)
            deviations.add("shortage", shortage)
            deviations.add("disparity", disparity)
            total_overhang = sum(self.calculate_potential_overhang(election))
            deviations.add("total_overhang", total_overhang)
            for cmp_election in elections:
                cmp_system = cmp_election.system
                if cmp_system["compare_with"]:
                    prefix = 'cmp_' + cmp_system["name"]
                    self.add_deviation(election,  cmp_election, prefix, deviations)
            self.other_seat_spec_measures(election, system, deviations)
            self.seats_minus_shares_measures(election, i, deviations)
            self.specific_measures(election, deviations)
        for m in deviations.keys():
            if m in self.stat:
                self.stat[m].update(deviations[m])

    def calculate_disparity(self, election):
        excess, shortage, disparity = 0, 0, 0
        for alloc, result in zip(election.ref_seat_alloc, election.results['all_grand_total']):
            diff = result - alloc
            disparity += abs(diff)
            excess += max(0, diff)
            shortage += max(0, -diff)
        return excess, shortage, disparity

    def calculate_party_disparity(self, election):
        disparity, excess, shortage = [], [], []
        for alloc, result in zip(election.ref_seat_alloc, election.results['all_grand_total']):
            disparity.append(result - alloc)
            excess.append(max(0, result-alloc))
            shortage.append(max(0, -(result-alloc)))
        return disparity, excess, shortage

    def calculate_potential_overhang(self, election):
        overhang = [max(0, cs - rss) for (cs, rss) in
                    zip(election.results['fixed_const_total'], election.ref_seat_alloc)]
        return overhang

    def calculate_negative_margins(self, election):
        seats = election.results["all_const_seats"]
        shares = election.ref_seat_shares
        neg_margins = []
        neg_parties = []
        for (srow,hrow) in zip(seats, shares):
            diff = [s - h for (s,h) in zip(srow, hrow)]
            maxdiff = max(diff)
            maxparty = diff.index(maxdiff)
            neg_margins.append(max(0, maxdiff - min(diff) - 1))
            neg_parties.append(maxparty)
        return neg_margins, neg_parties

    def neg_margin_matrix(self, neg_margins, neg_parties):
        const_party_margins = []
        const_party_margin_counts = []
        for neg_margin, neg_party in zip(neg_margins, neg_parties):
            pm = [0]*self.nparty
            pmc = [0]*self.nparty
            if neg_margin > 0:
                pm[neg_party] = neg_margin
                pmc[neg_party] = 1
            const_party_margins.append(pm)
            const_party_margin_counts.append(pmc)
        return add_totals(const_party_margins), add_totals(const_party_margin_counts)

    def seats_minus_shares_measures(self, election, i, deviations):
        for (funcname, (function, div_h)) in function_dict.items():
            measure = "sum_" + funcname ### KJ. bæta við að sleppa listum með atkvæði sem eru núll
            deviations.add(measure, self.sum_func(election, function, div_h, i))
        for (measure, function) in function_dict_party.items():
            for extension in ['const', 'nat', 'overall'] if self.party_votes_specified else ['overall']:
                measure_name = measure + '_' + extension
                deviations.add(measure_name, self.party_func(measure_name, election, function))

    def specific_measures(self, election, deviations):
        (slope, corr) = self.bias(election)
        deviations.add("min_seat_val", self.min_seat_val(election))
        deviations.add("bias_slope", slope)
        deviations.add("bias_corr", corr)

    def other_seat_spec_measures(self, election, system, deviations):
        for measure in ["dev_all_adj", "dev_all_fixed", "one_const"]:
            option = remove_prefix(measure, "dev_")
            comparison_system = system.generate_system(option)
            comparison_election = Election(comparison_system,
                                           election.m_votes,
                                           election.party_vote_info)
            comparison_election.run()
            self.add_deviation(election, comparison_election, measure, deviations)

    def add_deviation(self, election, comparison_election, prefix, deviations):
        tr = {'const': 'all_const_seats',
              'tot':   'all_const_total',
              'nat':   'all_nat_seats',
              'grand': 'all_grand_total'}
        extensions = ['const', 'tot']
        if self.party_votes_specified:
            extensions.extend(['nat', 'grand'])
        for extension in extensions:
            measure = prefix + '_' + extension
            key = tr[extension]
            result1 = election.results[key]
            result2 = comparison_election.results[key]
            deviations.add(measure, sum_abs_diff(result1, result2))

    def sum_func(self, election, function, div_h, election_number):
        measure = 0
        num_c = election.num_constituencies()
        for c in range(num_c):
            for p in range(self.nparty):
                s = election.results["all_const_seats"][c][p]
                if self.vote_table['votes'][c][p] == 0:
                    continue
                h = election.ref_seat_shares[c][p]
                if div_h:
                    if (self.base_allocations[election_number]['ref_seat_shares']
                        [num_c-1][p] == 0):
                            continue
                    if h == 0:
                        h = self.base_allocations[election_number]['ref_seat_shares'][c][p]
                measure += function(h, s)
        return measure

    def party_func(self, name, election, function):
        measure = 0
        for p in range(self.nparty):
            if name.endswith('overall'):
                s = election.results['all_grand_total'][p]
                h = election.total_ref_seat_shares[p]
            elif name.endswith('const'):
                s = election.results['all_const_total'][p]
                h = election.total_ref_seat_shares[p] - election.total_ref_nat[p]
            elif name.endswith('nat'):
                s = election.results['all_nat_seats'][p]
                h = election.total_ref_nat[p]
            if name.startswith('sum'):
                measure += function(h,s)
            elif name.startswith('max'):
                measure = max(measure, function(h,s))
            elif name.startswith('min'):
                measure = min(measure, function(h,s))
        return measure

    def run_sensitivity(self, votes):
        elections = self.election_handler.elections
        variation_coefficient = self.sim_settings["sens_cv"]
        sens_method = self.sim_settings["sens_method"]
        sens_votes = generate_votes(votes, variation_coefficient, sens_method)
        for (i, election) in enumerate(elections):
            sens_election = Election(election.system, sens_votes)
            sens_election.run()
            party_seats1 = election.desired_col_sums
            party_seats2 = sens_election.desired_col_sums
            party_seat_diff = sum_abs_diff(party_seats1, party_seats2)
            if party_seat_diff > 0:
                self.stat["party_sens"][i].update(party_seat_diff)
            else:
                list_seats1 = election.results['all_const_seats']
                list_seats2 = sens_election.results['all_const_seats']
                list_seat_diff = sum_abs_diff(list_seats1, list_seats2)
                self.stat["list_sens"][i].update(list_seat_diff)

    def bias(self, election):
        (slope,corr) = find_bias(election.results['all_const_seats'], election.ref_seat_shares)
        return slope,corr

    # Loosemore-Hanby
    def sum_abs(self, election):
        lh = sum([
            abs(election.ref_seat_shares[c][p] - election.results['all_const_seats'][c][p])
            for p in range(self.nparty)
            for c in range(election.num_constituencies())
        ])
        return lh

    # Minimized by Sainte Lague
    def sum_sq(self, election):
        ids = election.ref_seat_shares
        stl = sum([
            (ids[c][p] - election.results['all_const_seats'][c][p])**2/ids[c][p]
            for p in range(self.nparty)
            for c in range(election.num_constituencies())
            if ids[c][p] != 0
        ])
        return stl

    # Maximized by d'Hondt
    def min_seat_val(self, election):
        ids = election.ref_seat_shares
        dh_min = min([
            ids[c][p]/float(election.results['all_const_seats'][c][p])
            for p in range(self.nparty)
            for c in range(election.num_constituencies())
            if election.results['all_const_seats'][c][p] != 0
        ])
        return dh_min

    # Minimized by d'Hondt
    def sum_pos(self, election):
        ids = election.ref_seat_shares
        dh_sum = sum([
            max(0, ids[c][p] - election.results['all_const_seats'][c][p])/ids[c][p]
            for p in range(self.nparty)
            for c in range(election.num_constituencies())
            if ids[c][p] != 0
        ])
        return dh_sum

    def index_of_const_to_apply_randomness_to(self):
        sel_rand = self.sim_settings["selected_rand_constit"]
        if sel_rand not in self.constituencies or sel_rand == "All constituencies":
            index = -1
        else:
            index = self.constituencies.index(sel_rand)
        return index

    def attributes(self):
        builtins = {bool,int,float,complex,str,range,tuple,set,list,dict} # primary ones
        dictionary = copy(vars(self))
        class_keys = [k for (k,v) in dictionary.items() if type(v) not in builtins].copy()
        for key in class_keys:
            del dictionary[key]
        stat = dictionary['stat']
        for (key,val) in stat.items():
            if isinstance(val, list):
                for i in range(len(val)):
                    val[i] = vars(val[i]) if val[i] else {}
            else:
                stat[key] = vars(stat[key])
        return dictionary

class Sim_result:
    # Results from one simulation, or several combined simulations
    def __init__(self, dictionary):
        def ishistogram(x):
            return isinstance(x, dict) and 'histcounts' in x
        warnings_to_errors()
        for (key,val) in dictionary.items():
            if key=='stat':
                for statkey, statval in val.items():
                    if isinstance(statval,list):
                        for i in range(len(statval)):
                            if ishistogram(statval[i]):
                                statval[i] = Histogram(statval[i])
                            else:
                                statval[i] = Running_stats.from_dict(statval[i])
                    else:
                        if ishistogram(statval):
                            val[statkey] = Histogram(statval)
                        else:
                            val[statkey] = Running_stats.from_dict(statval)
            setattr(self, key, val)

        # self.data = [{} for _ in range(self.nsys)]
        # self.seat_data = [{} for _ in range(self.nsys + 1)]
        # self.vote_data = [{} for _ in range(self.nsys)]

    def combine(self, sim_result):
        self.iteration += sim_result.iteration
        self.total_time += sim_result.total_time
        nclist = [len(sys["constituencies"]) for sys in self.systems]
        for measure in VOTE_MEASURES:
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in SEAT_MEASURES:
            for (i,nc) in enumerate(nclist):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in SENS_MEASURES:
            for i in range(self.nsys):
                self.stat[measure][i].combine(sim_result.stat[measure][i])
        np = self.nparty
        for measure in HISTOGRAM_MEASURES:
            for s in range(self.nsys):
                for p in range(np):
                    i = s*np + p
                    self.stat[measure][i].combine(sim_result.stat[measure][i])
        for measure in self.MEASURES:  # Was MEASURES in earlier version
            self.stat[measure].combine(sim_result.stat[measure])
        for measure in PARTY_MEASURES:
            for i in range(self.nsys):
                self.stat[measure][i].combine(sim_result.stat[measure][i])

        extensions = ['const', 'tot']
        if self.party_votes_specified:
            extensions.extend(['nat', 'grand'])
        for cmp_system in self.systems:
            if cmp_system["compare_with"]:
                for extension in extensions:
                    measure = "cmp_" + cmp_system["name"] + "_" + extension
                    self.stat[measure].combine(sim_result.stat[measure])

    def analyze_vote_data(self):
        for m in VOTE_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                self.vote_data[i][m] = dict((s, dd[s]) for s in self.STAT_LIST)
                if m == "neg_margin_count":
                    for (key,val) in self.vote_data[i][m].items():
                        self.vote_data[i][m][key][-1] = \
                            [x/self.nconst for x in val[-1]]

    def analyze_seat_data(self):
        for m in SEAT_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                D = {}
                for s in self.STAT_LIST:
                    D[s] = dd[s]
                self.seat_data[i][m] = D

    def analyze_general(self):
        for m in self.MEASURES:
            dd = self.find_datadict(self.stat[m], self.MEASURE_LIST)
            for i in range(self.nsys):
                self.data[i][m] = dict((s, dd[s][i]) for s in self.MEASURE_LIST)

        for m in PARTY_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                self.party_data[i][m] = dict((s, dd[s]) for s in self.STAT_LIST)
        #self.disparity_data = [self.stat['party_disparity'][sys].keep
        #                       for sys in range(self.nsys)]'
        for m in HISTOGRAM_MEASURES:
            self.histogram_data[m] = [s.get() for s in self.stat[m]]

    def analysis(self):
        # Calculate averages and variances of various quality measures.
        self.data = [{} for _ in range(self.nsys)]
        self.seat_data = [{} for _ in range(self.nsys + 1)]
        self.vote_data = [{} for _ in range(self.nsys)]
        self.party_data = [{} for _ in range(self.nsys)]
        self.histogram_data = {}
        if hasattr(self, 'sensitivity') and self.sensitivity:
            self.list_sensitivity = self.gethistograms("list")
            self.party_sensitivity = self.gethistograms("party")
        else:
            self.analyze_vote_data()
            self.analyze_seat_data()
            self.analyze_general()
            self.seat_data[-1] = self.vote_data[0]  # used by excel_util
        # Það er villa sem á eftir að leiðrétta þegar búið er að "mergja" Excel
        # útskrift (des. 2021). Vote-data er bara skrifað út fyrir fyrsta kerfið
        # í seat_data[-1] en ef sum kerfin eru með sameinuð kjördæmi (í "All")
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

    def get_result_web(self, parallel):
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
            "party_data":       self.party_data,
            "histogram_data":   self.histogram_data,
            "vote_table":       self.vote_table,
            "base_allocations": self.base_allocations,
            "data":         [{
                "name":           self.systems[sysnr]["name"],
                "method":         self.systems[sysnr]["adjustment_method"],
                "measures":       self.data[sysnr],
                "seat_measures":  self.seat_data[sysnr]
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
