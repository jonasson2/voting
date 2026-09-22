# import logging
from datetime import datetime
from measure_groups import MeasureGroups, function_dict, function_dict_party
from voting import Election
from dictionaries import SEAT_MEASURES, VOTE_MEASURES, CONSTANTS, SENS_MEASURES
from dictionaries import HISTOGRAM_MEASURES, PARTY_MEASURES
from dictionaries import STATISTICS_HEADINGS, EXCEL_HEADINGS
from electionHandler import ElectionHandler
from generate_votes import generate_votes, generate_corr_votes
from running_stats import Running_stats
#from system import System
from table_util import add_totals, find_percentages, find_bias
from table_util import np_add_total, np_add_totals
from util import hms, count
from copy import copy, deepcopy
from util import remove_prefix, sum_abs_diff
from histogram import Histogram
from sim_measures import add_vuedata
from randomness import make_rng
import numpy as np
from numpy import vstack

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
        self["gen_method"] = "log-normal"
        self["const_rsd"] = CONSTANTS["CoeffVar"]
        self["const_corr"] = CONSTANTS["ConstCorr"]
        self["party_vote_rsd"] = CONSTANTS["CoeffVar"]/2
        self["party_vote_corr"] = CONSTANTS["PartyVoteCorr"]
        self["use_thresholds"] = True
        self["scaling"] = "both"
        self["sensitivity"] = False
        self["random_seed"] = None

    def abs(q, s):      return abs(q - s)
    def sq(q, s):       return (q - s)**2


def simulation_vote_table(source, minimum_one=False):
    table = deepcopy(source)
    independent = table.get("independent_candidates", [False] * len(table["parties"]))
    keep = [p for p, flag in enumerate(independent) if not flag]
    if not keep:
        raise ValueError("A simulation needs at least one party after excluding independent candidates.")
    if any(independent):
        table["pruned"] = [
            pruned + sum(vote for vote, flag in zip(row, independent) if flag)
            for pruned, row in zip(table.get("pruned", [0] * len(table["votes"])), table["votes"])]
        for key in ("parties", "party_names", "independent_candidates"):
            if key in table:
                table[key] = [table[key][p] for p in keep]
        table["votes"] = [[row[p] for p in keep] for row in table["votes"]]
        info = table["party_vote_info"]
        if info["specified"]:
            info["pruned"] = info.get("pruned", 0) + sum(
                vote for vote, flag in zip(info["votes"], independent) if flag)
            info["votes"] = [info["votes"][p] for p in keep]
    if minimum_one:
        table["votes"] = np.maximum(table["votes"], 1).tolist()
    return table


def normalize_constituency_votes(votes, reference_votes):
    """Preserve each constituency's source total after varying party shares."""
    votes = np.asarray(votes, dtype=float)
    reference_totals = np.asarray(reference_votes, dtype=float).sum(axis=1)
    generated_totals = votes.sum(axis=1)
    if np.any((generated_totals == 0) & (reference_totals != 0)):
        raise ValueError(
            "Generated constituency votes cannot be normalized from zero.")
    factors = np.divide(
        reference_totals,
        generated_totals,
        out=np.zeros_like(reference_totals),
        where=generated_totals != 0,
    )
    return (votes * factors[:, None]).tolist()


class Simulation():
    # Simulate a set of elections in a single thread
    def __init__(self, sim_settings, systems, vote_table, nr=0, start_iteration=0):
        warnings_to_errors()
        use_thresholds = sim_settings['use_thresholds']
        self.sim_settings = sim_settings
        self.random_seed = sim_settings.get("random_seed")
        self.start_iteration = start_iteration
        self.next_global_iteration = start_iteration
        self.regional_simulation = bool(vote_table.get("regions"))
        vote_table = simulation_vote_table(vote_table, self.regional_simulation)
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
        self.const_rsd = sim_settings["const_rsd"]
        self.const_corr = sim_settings["const_corr"]
        self.party_vote_rsd = sim_settings["party_vote_rsd"]
        self.party_vote_corr = sim_settings["party_vote_corr"]
        self.terminate = False
        # ------- Following properties are only used by excel_util.py
        self.constituencies = [c['name'] for c in vote_table["constituencies"]]
        self.nsys = len(self.reference_handler.elections)
        self.nparty = len(self.parties)
        self.nconst = len(self.constituencies)
        self.sensitivity = sim_settings["sensitivity"]
        # -------- Following is used for plotting
        #self.disparity_data = [pd.DataFrame(columns=self.parties) for sys in range(self.nsys)]
        # --------
        self.iteration = 0
        self.total_time = 0
        self.time_left = 0
        self.initialize_stat_counters()
        self.set_election_rngs(self.reference_handler, 0, purpose=2)
        self.reference_handler.run_elections(use_thresholds)
        self.run_initial_elections()

    def rng(self, iteration, purpose, system_index=0):
        return make_rng(
            self.random_seed,
            (iteration, purpose, system_index),
        )

    def set_election_rngs(self, handler, iteration, purpose):
        for index, election in enumerate(handler.elections):
            election.rng = self.rng(iteration, purpose, index)

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
            shape = ns + (1 if ns >= 2 else 0)
            self.stat[measure] = Running_stats(shape, parallel, measure)
        for measure in HISTOGRAM_MEASURES:
            self.stat[measure] = [None]*ns*np
            for i in range(ns*np):
                self.stat[measure][i] = Histogram()
        for measure in PARTY_MEASURES:
            self.stat[measure] = [None] * ns
            for s in range(ns):
                #store = measure=='party_disparity'
                self.stat[measure][s] = Running_stats(np, parallel, measure)

    def run_initial_elections(self):
        for election in self.reference_handler.elections:
            election.calculate_ref_seat_shares(self.sim_settings["scaling"])
            disparity, excess, shortage = self.calculate_party_disparity(election)
            party_overhang = self.calculate_potential_overhang(election)
            neg_margins, neg_parties = \
                self.calculate_negative_margins(election, election.ref_seat_shares)
            const_party_margins, cpm_counts = self.neg_margin_matrix(
                neg_margins, neg_parties)
            ids = self.extended_ref_seat_shares(election)
            self.base_allocations.append({
                "fixed_seats": election.results["fix"],
                "adj_seats":   election.results["adj"],
                "total_seats": election.results["all"],
                "total_seat_percentages": find_percentages(election.results["all"]),
                "ref_seat_alloc": election.results["ref_seat_alloc"],
                "party_disparity": disparity,
                "party_excess": excess,
                "party_shortage": shortage,
                "party_overhang": party_overhang,
                "neg_margins": const_party_margins,
                "neg_margin_count": cpm_counts,
                "ref_seat_shares": ids.tolist(),
            })

    def extended_ref_seat_shares(self, election):
        shares = np_add_totals(election.ref_seat_shares)
        if self.party_votes_specified:
            shares = vstack((shares, np_add_total(election.total_ref_nat)))
            shares = vstack((shares, shares[-2] + shares[-1]))
        return shares

    def simulate(self, tasknr=0, monitor=None):
        # Simulate many elections.
        if self.sim_count == 0:
            return
        begin_time = datetime.now()
        for i in range(self.sim_count):
            self.iteration = i + 1
            global_iteration = self.start_iteration + i
            votes, party_votes = self.generate_simulated_votes(global_iteration)
            self.run_and_collect_measures(
                votes, party_votes, global_iteration)  # This allocates
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
        iteration = self.next_global_iteration
        while True:
            yield self.generate_simulated_votes(iteration)
            iteration += 1

    def generate_simulated_votes(self, iteration):
        rng = self.rng(iteration, purpose=0)
        if self.distribution == 'log-normal':
            votes, party_votes = generate_corr_votes(
                self.election_handler.votes,
                self.const_rsd,
                self.const_corr,
                self.election_handler.party_vote_info["votes"],
                self.party_vote_rsd,
                self.party_vote_corr,
                rng,
            )
        else:
            votes = generate_votes(
                self.election_handler.votes, self.const_rsd,
                self.distribution, rng)
            if self.party_votes_specified:
                party_votes = generate_votes(
                    [self.election_handler.party_vote_info["votes"]],
                    self.party_vote_rsd, self.distribution, rng)[0]
            else:
                party_votes = None
        if self.regional_simulation:
            votes = np.maximum(votes, 1).tolist()
        votes = normalize_constituency_votes(
            votes, self.election_handler.votes)
        return votes, party_votes

    def run_and_collect_measures(self, votes, party_votes, iteration=None):
        if iteration is None:
            iteration = self.next_global_iteration
            self.next_global_iteration += 1
        use_thresholds = self.sim_settings["use_thresholds"]
        self.set_election_rngs(self.election_handler, iteration, purpose=1)
        self.election_handler.run_elections(use_thresholds, votes, party_votes)
        if self.sensitivity:
            self.run_sensitivity(votes, iteration)
        else:
            self.collect_vote_measures()
            self.collect_seat_measures()
            self.collect_party_measures()
            self.collect_general_measures()

    def collect_vote_measures(self):
        for (i,election) in enumerate(self.election_handler.elections):
            votes = np_add_totals(election.votes)
            if self.party_votes_specified:
                votes = np.vstack((votes, np_add_total(election.nat_votes)))
            vote_percentages = find_percentages(votes)
            #const_party_disparity = self.calculate_const_party_disparity(election)
            #self.stat["neg_margin"][i].update()
            self.stat["sim_votes"][i].update(votes)
            self.stat["sim_vote_percentages"][i].update(vote_percentages)

    def collect_seat_measures(self):
        for (i,election) in enumerate(self.election_handler.elections):
            election.calculate_ref_seat_shares(
                self.sim_settings["scaling"], id=self.iteration)
            ids = self.extended_ref_seat_shares(election)
            cs = np.array(election.results["fix"])
            ts = np.array(election.results["all"])
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
            self.stat["party_ref_seat_shares"][i].update(
                election.total_ref_seat_shares)
            self.stat["nat_vote_percentages"][i].update(nat_vote_percentages)
            self.stat["party_total_seats"][i].update(election.results["all_grand_total"])
            self.stat["ref_seat_alloc"][i].update(election.ref_seat_alloc)
            self.stat["party_disparity"][i].update(disparity)
            self.stat["party_excess"][i].update(excess)
            self.stat["party_shortage"][i].update(shortage)
            self.stat["party_overhang"][i].update(party_overhang)
            for p in range(self.nparty):
                self.stat["disparity_count"][i*self.nparty + p].update(disparity[p])
                self.stat["overhang_count"][i*self.nparty + p].update(
                    party_overhang[p])

    def collect_general_measures(self):
        deviations = Collect()
        ref_elections = self.reference_handler.elections
        elections = self.election_handler.elections
        for i, (ref_election, election) in enumerate(zip(ref_elections, elections)):
            system = election.system
            self.add_deviation(election, ref_election, "dev_ref", deviations)
            neg_margins, neg_parties = \
                self.calculate_negative_margins(election, election.ref_seat_shares)
            const_party_margins, cpm_counts = self.neg_margin_matrix(neg_margins, neg_parties)
            self.stat["neg_margin"][i].update(const_party_margins)
            self.stat["neg_margin_count"][i].update(cpm_counts)
            deviations.add("max_neg_margin", max(neg_margins))
            deviations.add("freq_neg_margin", count(neg_margins))
            for measure, value in election.entropies().items():
                deviations.add(measure, value)
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
                values = deviations[m]
                if self.nsys >= 2:
                    values = values + [values[0] - values[1]]
                self.stat[m].update(values)

    def calculate_disparity(self, election):
        excess, shortage, disparity = 0, 0, 0
        for alloc, result in zip(election.results['ref_seat_alloc'],
                                 election.results['all_grand_total']):
            diff = result - alloc
            disparity += abs(diff)
            excess += max(0, diff)
            shortage += max(0, -diff)
        return excess, shortage, disparity

    def calculate_party_disparity(self, election):
        disparity, excess, shortage = [], [], []
        for alloc, result in zip(election.results["ref_seat_alloc"],
                                 election.results["all_grand_total"]):
            disparity.append(result - alloc)
            excess.append(max(0, result-alloc))
            shortage.append(max(0, -(result-alloc)))
        return disparity, excess, shortage

    def calculate_potential_overhang(self, election):
        return [max(0, fixed - reference) for fixed, reference in
                zip(election.results['fixed_const_total'],
                    election.results['ref_seat_alloc'])]

    def calculate_negative_margins(self, election, ref_seat_shares):
        seats = election.results["all_const_seats"]
        neg_margins = []
        neg_parties = []
        for (srow,hrow) in zip(seats, ref_seat_shares):
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
        deviations.add(
            "max_overrepresentation",
            self.max_overrepresentation(election),
        )
        deviations.add(
            "max_underrepresentation",
            self.max_underrepresentation(election),
        )
        deviations.add(
            "geographical_displacement",
            self.geographical_seat_displacement(election),
        )
        deviations.add("bias_slope", slope)
        deviations.add("bias_corr", corr)

    @staticmethod
    def geographical_seat_displacement(election):
        """Return seats displaced from a vote-proportional geography."""
        constituency_votes = (
            election.votes.sum(axis=1) + np.asarray(election.pruned_votes))
        total_votes = constituency_votes.sum()
        if total_votes == 0:
            return 0
        seats = np.asarray(election.final_row_sums)
        reference = seats.sum() * constituency_votes / total_votes
        return np.abs(seats - reference).sum() / 2

    def other_seat_spec_measures(self, election, system, deviations):
        for measure in ["dev_all_adj", "dev_all_fixed", "one_const"]:
            option = remove_prefix(measure, "dev_")
            special_rules = system.get("special_rules", "none")
            if (special_rules != "none" or election.has_regions
                    or election.has_flexible_adj_seats):
                # These counterfactual layouts do not define how special rules,
                # regions or constituency seat ranges should be changed.
                self.add_deviation(
                    election, election, measure, deviations)
                continue
            comparison_system = system.generate_system(option)
            comparison_election = Election(comparison_system,
                                           election.votes,
                                           election.party_vote_info,
                                           pruned_votes=election.pruned_votes,
                                           rng=election.rng.duplicate())
            comparison_election.assign_seats(election.use_thresholds)
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
        num_c = election.nconst
        for c in range(num_c):
            for p in range(self.nparty):
                s = election.results["all_const_seats"][c][p]
                if election.votes[c][p] == 0:
                    continue
                h = election.ref_seat_shares[c][p]
                if div_h:
                    if h == 0:
                        h = self.base_allocations[election_number][
                            'ref_seat_shares'][c][p]
                    if h == 0:
                        continue
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
                h = election.total_ref_const[p]
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

    def run_sensitivity(self, votes, iteration):
        elections = self.election_handler.elections
        relative_SD = self.sim_settings["sens_rsd"]
        sens_method = self.sim_settings["sens_method"]
        sens_votes = generate_votes(
            votes, relative_SD, sens_method, self.rng(iteration, purpose=3))
        for (i, election) in enumerate(elections):
            sens_election = Election(
                election.system, sens_votes,
                rng=self.rng(iteration, purpose=4, system_index=i))
            sens_election.assign_seats(election.use_thresholds)
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
        (slope,corr) = find_bias(
            election.results['all_const_seats'], election.ref_seat_shares)
        return slope,corr

    # Minimized by D'Hondt in an unconstrained single-constituency allocation.
    def max_overrepresentation(self, election):
        ratios = []
        for seats, references in zip(
                election.results['all_const_seats'],
                election.ref_seat_shares):
            for seat, reference in zip(seats, references):
                if seat == 0:
                    continue
                if reference == 0:
                    raise RuntimeError(
                        "Relative over-representation is undefined when a "
                        "list with zero reference seats receives a seat.")
                ratios.append(seat / reference)
        return max(ratios, default=0)

    # Minimized by Adams in an unconstrained single-constituency allocation.
    def max_underrepresentation(self, election):
        return max((
            max(0, (reference - seat) / reference)
            for seats, references in zip(
                election.results['all_const_seats'],
                election.ref_seat_shares)
            for seat, reference in zip(seats, references)
            if reference != 0
        ), default=0)

    def attributes(self):
        builtins = {bool,int,float,complex,str,range,tuple,set,list,dict} # primary ones
        dictionary = copy(vars(self))
        class_keys = [
            k for (k,v) in dictionary.items()
            if not isinstance(v, tuple(builtins))
        ].copy()
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
    # Not used in Germany simulations
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

    def analyze_vote_data(self):
        for m in VOTE_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                self.vote_data[i][m] = dict((s, dd[s]) for s in self.STAT_LIST)
                # if m == "neg_margin_count":
                #     for (key,val) in self.vote_data[i][m].items():
                #         self.vote_data[i][m][key][-1] = \
                #             [x/self.nconst for x in val[-1]]

    def analyze_seat_data(self):
        for m in SEAT_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                D = {}
                for s in self.STAT_LIST:
                    D[s] = dd[s]
                self.seat_data[i][m] = D

    def analyze_general(self):
        self.paired_data = {}
        for m in self.MEASURES:
            dd = self.find_datadict(self.stat[m], self.MEASURE_LIST)
            for i in range(self.nsys):
                self.data[i][m] = dict((s, dd[s][i]) for s in self.MEASURE_LIST)
            if self.nsys >= 2:
                self.paired_data[m] = {
                    stat: values[-1] for stat, values in dd.items()
                }

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
            "paired_data":      getattr(self, "paired_data", {}),
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
