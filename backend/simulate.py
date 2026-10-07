from reference_measures import list_measures, selected_scalings, primary_scaling
# import logging
from datetime import datetime
from measure_groups import MeasureGroups
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
from table_util import entropy
from util import hms, count
from copy import copy, deepcopy
from util import remove_prefix, sum_abs_diff
from histogram import Histogram
from sim_measures import add_vuedata
from randomness import make_rng
from sensitivity import (
    generate_perturbations, seat_displacements, sensitivity_covs,
    sensitivity_statistics, SINGLE_LIST_MEASURES, single_list_perturbations,
    single_list_category)
import numpy as np
from numpy import vstack
from math import exp

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
        self["entropy_score"] = True
        self["scaling"] = ["const"]
        self["show_additional"] = False
        self["show_single_seat"] = False
        self["single_list_sensitivity"] = False
        self["single_list_simulation_count"] = 20
        self["sensitivity"] = False
        self["sensitivity_simulation_count"] = 3
        self["sensitivity_gen_method"] = "uniform"
        self["sensitivity_covs"] = [0.1, 0.3, 1]
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
        self.scalings = selected_scalings(sim_settings["scaling"])
        self.primary_scaling = primary_scaling(sim_settings)
        self.random_seed = sim_settings.get("random_seed")
        self.start_iteration = start_iteration
        self.next_global_iteration = start_iteration
        self.regional_simulation = bool(vote_table.get("regions"))
        vote_table = simulation_vote_table(vote_table, self.regional_simulation)
        self.vote_table = vote_table
        self.reference_handler = ElectionHandler(vote_table, systems, use_thresholds)
        self.election_handler = ElectionHandler(vote_table, systems, use_thresholds)
        self.sensitivity = (sim_settings["sensitivity"]
                            or sim_settings.get("single_list_sensitivity", False))
        self.sensitivity_measures = (
            (SENS_MEASURES if sim_settings["sensitivity"] else [])
            + (SINGLE_LIST_MEASURES if sim_settings.get("single_list_sensitivity") else []))
        self.sensitivity_handler = (
            ElectionHandler(vote_table, systems, use_thresholds)
            if self.sensitivity else None)
        self.systems = [election.system for election in self.election_handler.elections]
        self.party_votes_specified = self.vote_table["party_vote_info"]["specified"]
        self.measure_groups = MeasureGroups(
            systems, self.party_votes_specified, nr,
            include_entropy_score=sim_settings["entropy_score"], scalings=self.scalings)
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
        self.sensitivity_simulation_count = sim_settings[
            "sensitivity_simulation_count"]
        self.sensitivity_distribution = sim_settings[
            "sensitivity_gen_method"]
        self.sensitivity_covs = (
            sensitivity_covs(sim_settings["sensitivity_covs"])
            if self.sensitivity else [])
        self.entropy_score_available = [
            election.entropy_score_available()
            for election in self.election_handler.elections
        ]
        reference = self.election_handler.elections[0]
        self.entropy_relative_available = [
            self.entropy_score_available[0] and available
            and election.system["adj_alloc_divider"]
                == reference.system["adj_alloc_divider"]
            and election.votes.shape == reference.votes.shape
            and election.total_const_seats == reference.total_const_seats
            for election, available in zip(
                self.election_handler.elections, self.entropy_score_available)
        ]
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
        if self.sensitivity:
            sensitivity_shape = (
                len(self.sensitivity_covs),
                ns,
            )
            for measure in self.sensitivity_measures:
                self.stat[measure] = Running_stats(
                    sensitivity_shape, parallel, measure)
                self.stat[measure + "_perturbations"] = Running_stats(
                    sensitivity_shape, True, measure)
        for measure in self.MEASURES:
            self.stat[measure] = Running_stats(ns, parallel, measure)
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
            election.calculate_ref_seat_shares(self.primary_scaling)
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
            rng = make_rng(self.random_seed, (global_iteration,))
            votes, party_votes = self.generate_simulated_votes(global_iteration, rng)
            self.run_and_collect_measures(
                votes, party_votes, global_iteration, rng)  # This allocates
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

    def generate_simulated_votes(self, iteration, rng=None):
        if rng is None:
            rng = make_rng(self.random_seed, (iteration,))
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

    def run_and_collect_measures(self, votes, party_votes, iteration=None, rng=None):
        if iteration is None:
            iteration = self.next_global_iteration
            self.next_global_iteration += 1
        if rng is None:
            rng = make_rng(self.random_seed, (iteration,))
        use_thresholds = self.sim_settings["use_thresholds"]
        for election in self.election_handler.elections:
            election.rng = rng
        self.election_handler.run_elections(use_thresholds, votes, party_votes)
        self.collect_vote_measures()
        self.collect_seat_measures()
        self.collect_party_measures()
        self.collect_general_measures(iteration)
        if self.sim_settings["sensitivity"]:
            self.run_sensitivity(votes, party_votes, rng)
        if self.sim_settings.get("single_list_sensitivity"):
            self.run_single_list_sensitivity(votes, party_votes, rng)

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
                self.primary_scaling, id=self.iteration)
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

    def collect_general_measures(self, replicate=None):
        deviations = Collect()
        entropy_cache = {}
        ref_elections = self.reference_handler.elections
        elections = self.election_handler.elections
        if self.sim_settings["entropy_score"] and self.nsys > 1:
            reference = elections[0]
            reference_entropy = entropy(
                np.maximum(reference.votes, 1),
                reference.results["all_const_seats"],
                reference.system.get_generator("adj_alloc_divider"))
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
            if self.sim_settings["entropy_score"]:
                score = election.entropy_score(entropy_cache, replicate=replicate)
                deviations.add(
                    "entropy_score", 0 if score is None else score)
                if self.nsys > 1:
                    relative = 0
                    if self.entropy_relative_available[i]:
                        actual_entropy = entropy(
                            np.maximum(election.votes, 1),
                            election.results["all_const_seats"],
                            election.system.get_generator("adj_alloc_divider"))
                        relative = exp(actual_entropy - reference_entropy)
                    deviations.add("entropy_relative", relative)
            excess, shortage, disparity = self.calculate_disparity(election)
            deviations.add("excess", excess)
            deviations.add("shortage", shortage)
            deviations.add("disparity", disparity)
            total_overhang = sum(self.calculate_potential_overhang(election))
            deviations.add("total_overhang", total_overhang)
            for cmp_election in elections:
                cmp_system = cmp_election.system
                prefix = 'cmp_' + cmp_system["name"]
                self.add_deviation(election, cmp_election, prefix, deviations)
            self.other_seat_spec_measures(election, system, deviations)
            self.party_reference_measures(election, deviations)
            self.specific_measures(election, deviations)
            self.reference_measures(election, deviations)
        for m in deviations.keys():
            if m in self.stat:
                self.stat[m].update(deviations[m])

    def reference_measures(self, election, deviations):
        seats = np.asarray(election.results["all_const_seats"])
        totals = seats.sum()
        for scaling in dict.fromkeys(["const", *self.scalings]):
            reference = (election.ref_seat_shares if scaling == self.primary_scaling
                         else election.reference_seats(scaling))
            values = list_measures(seats, reference)
            if scaling == "const":
                deviations.add("lh_lists", values["deviation"] / (2 * totals) if totals else 0)
                deviations.add("local_squared", values["relative_squared"])
            if scaling in self.scalings:
                for key, value in values.items():
                    deviations.add(f"{scaling}_{key}", value)
        party_seats = np.asarray(election.results["all_grand_total"])
        difference = party_seats - election.fractional_party_seats
        deviations.add("lh_parties", np.abs(difference).sum() / (2 * party_seats.sum()))
        deviations.add("party_total_surplus", max(0, difference.max()))
        deviations.add("party_total_shortfall", max(0, -difference.min()))
        deviations.add("lh_constituencies",
                       self.geographical_seat_displacement(election) / totals if totals else 0)

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

    def party_reference_measures(self, election, deviations):
        allocated = np.asarray(election.results["all_grand_total"])
        deviations.add("sum_sq_party_overall",
                       ((allocated - election.fractional_party_seats) ** 2).sum())
        if self.party_votes_specified:
            for extension, key, reference in (
                    ("const", "all_const_total", election.total_ref_const),
                    ("nat", "all_nat_seats", election.total_ref_nat)):
                difference = np.asarray(election.results[key]) - reference
                deviations.add(f"sum_abs_party_{extension}", np.abs(difference).sum() / 2)
                deviations.add(f"sum_sq_party_{extension}", (difference ** 2).sum())

    def specific_measures(self, election, deviations):
        slope, corr = self.bias(election)
        deviations.add("constituency_disparity", self.constituency_disparity(election))
        deviations.add("bias_slope", slope)
        deviations.add("bias_corr", corr)

    @staticmethod
    def constituency_vote_totals(election):
        return (
            election.votes.sum(axis=1) + np.asarray(election.pruned_votes))

    @staticmethod
    def geographical_seat_displacement(election):
        """Return seats displaced from a vote-proportional geography."""
        constituency_votes = Simulation.constituency_vote_totals(election)
        total_votes = constituency_votes.sum()
        if total_votes == 0:
            return 0
        seats = np.asarray(election.final_row_sums)
        reference = seats.sum() * constituency_votes / total_votes
        return np.abs(seats - reference).sum() / 2

    @staticmethod
    def constituency_disparity(election):
        """Ratio of the highest to lowest constituency votes per seat."""
        votes = Simulation.constituency_vote_totals(election)
        seats = np.asarray(election.final_row_sums)
        if (votes <= 0).any() or (seats <= 0).any():
            raise ValueError(
                "Constituency disparity requires positive votes and seats "
                "in every constituency.")
        votes_per_seat = votes / seats
        return float(votes_per_seat.max() / votes_per_seat.min())

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
            difference = sum_abs_diff(result1, result2)
            if difference is not None and prefix.startswith('cmp_'):
                difference /= 2
            deviations.add(measure, difference)

    def run_sensitivity(self, votes, party_votes, rng):
        """Retain displacements and change indicators, plus each outer mean."""
        for election in self.sensitivity_handler.elections:
            election.rng = rng
        shape = (self.sensitivity_simulation_count,
                 len(self.sensitivity_covs), self.nsys)
        between_values = np.empty(shape)
        within_values = np.empty(shape)
        for cov_index, cov in enumerate(self.sensitivity_covs):
            perturbed_votes, perturbed_party_votes = generate_perturbations(
                votes,
                party_votes,
                self.sensitivity_simulation_count,
                cov,
                self.sensitivity_distribution,
                rng,
            )
            for minor_index in range(self.sensitivity_simulation_count):
                minor_party_votes = (
                    None if perturbed_party_votes is None
                    else perturbed_party_votes[minor_index])
                self.sensitivity_handler.run_elections(
                    self.sim_settings["use_thresholds"],
                    perturbed_votes[minor_index],
                    minor_party_votes,
                )
                between, within = seat_displacements(
                    self.election_handler.elections,
                    self.sensitivity_handler.elections,
                )
                between_values[minor_index, cov_index] = between
                within_values[minor_index, cov_index] = within

        for measure, values in (
                ("sensitivity_between_parties", between_values),
                ("sensitivity_within_parties", within_values),
                ("sensitivity_list_only_change",
                 (between_values == 0) & (within_values > 0)),
                ("sensitivity_party_change", between_values > 0)):
            self.stat[measure].update(values.mean(axis=0))
            for perturbation in values:
                self.stat[measure + "_perturbations"].update(perturbation)

    def run_single_list_sensitivity(self, votes, party_votes, rng):
        for election in self.sensitivity_handler.elections:
            election.rng = rng
        count = self.sim_settings["single_list_simulation_count"]
        values = np.zeros((len(SINGLE_LIST_MEASURES), count,
                           len(self.sensitivity_covs), self.nsys))
        for cov_index, cov in enumerate(self.sensitivity_covs):
            for inner, (constituency, party, perturbed) in enumerate(
                    single_list_perturbations(votes, count, cov,
                                              self.sensitivity_distribution, rng)):
                self.sensitivity_handler.run_elections(
                    self.sim_settings["use_thresholds"], perturbed.tolist(), party_votes)
                for index, (base, changed) in enumerate(zip(
                        self.election_handler.elections, self.sensitivity_handler.elections)):
                    category = single_list_category(base, changed, constituency, party)
                    values[category, inner, cov_index, index] = 1
        for measure, outcomes in zip(SINGLE_LIST_MEASURES, values):
            self.stat[measure].update(outcomes.mean(axis=0))
            for outcome in outcomes:
                self.stat[measure + "_perturbations"].update(outcome)

    def bias(self, election):
        (slope,corr) = find_bias(
            election.results['all_const_seats'], election.ref_seat_shares)
        return slope,corr

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

        if not hasattr(self, "sensitivity_measures"):
            self.sensitivity_measures = SENS_MEASURES if self.sensitivity else []

        # Completed parallel web results contain analyzed data without stat.
        if self.sensitivity and "stat" in dictionary and any(
                measure + "_perturbations" not in self.stat
                for measure in self.sensitivity_measures):
            raise ValueError(
                "These saved sensitivity statistics lack individual perturbation "
                "statistics. Rerun the simulation to calculate their uncertainty.")

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
        if self.sensitivity:
            for measure in self.sensitivity_measures:
                self.stat[measure].combine(sim_result.stat[measure])
                self.stat[measure + "_perturbations"].combine(
                    sim_result.stat[measure + "_perturbations"])
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
        for m in self.MEASURES:
            dd = self.find_datadict(self.stat[m], self.MEASURE_LIST)
            for i in range(self.nsys):
                self.data[i][m] = {
                    s: ("∞" if s in {"avg", "max"} else "–")
                    if self.stat[m].infinite[i] else dd[s][i]
                    for s in self.MEASURE_LIST}


        for m in PARTY_MEASURES:
            for (i, sm) in enumerate(self.stat[m]):
                dd = self.find_datadict(sm, self.STAT_LIST)
                self.party_data[i][m] = dict((s, dd[s]) for s in self.STAT_LIST)
        #self.disparity_data = [self.stat['party_disparity'][sys].keep
        #                       for sys in range(self.nsys)]'
        for m in HISTOGRAM_MEASURES:
            self.histogram_data[m] = [s.get() for s in self.stat[m]]

    def analyze_sensitivity(self):
        self.sensitivity_data = {
            "covs": [100 * cov for cov in self.sensitivity_covs],
        }
        for measure in self.sensitivity_measures:
            self.sensitivity_data[measure] = sensitivity_statistics(
                self.stat[measure], self.stat[measure + "_perturbations"])

    def analysis(self):
        # Calculate averages and variances of various quality measures.
        self.data = [{} for _ in range(self.nsys)]
        self.seat_data = [{} for _ in range(self.nsys + 1)]
        self.vote_data = [{} for _ in range(self.nsys)]
        self.party_data = [{} for _ in range(self.nsys)]
        self.histogram_data = {}
        self.analyze_vote_data()
        self.analyze_seat_data()
        self.analyze_general()
        self.seat_data[-1] = self.vote_data[0]  # used by excel_util
        if self.sensitivity:
            self.analyze_sensitivity()
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
            "entropy_score_available": self.entropy_score_available,
            "entropy_relative_available": self.entropy_relative_available,
            "sensitivity_data": getattr(self, "sensitivity_data", None),
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
