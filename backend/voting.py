# coding:utf-8
"""
This module contains the core voting system logic.
"""

from table_util import entropy, add_total_column
from apportion import apportion1d_general, threshold_drop
from dictionaries import ADJUSTMENT_METHODS
from dictionaries import FLEXIBLE_ADJUSTMENT_METHODS
from dictionaries import ADJUSTMENT_PREPARATION_METHODS
from dictionaries import DEMO_TABLE_FORMATS
from dictionaries import ADJUSTMENT_PREPARATION_DEMO_TABLE_FORMATS
import numpy as np
from methods import danish
from vote_table import check_regions

class Election:
    """A single election."""

    def __init__(self, system, votes, party_vote_info=None, vote_table_name='',
                 pruned_votes=None, adjustment_seat_info=None, regions=None,
                 independent_candidates=None, rng=None):
        if party_vote_info is None:
            party_vote_info = {'name':'-', 'num_fixed_seats':0, 'num_adj_seats':0,
                               'votes':[],'specified':False, 'total':0, 'pruned':0}
        self.nconst = len(system["constituencies"])
        self.nparty = len(system["parties"])
        self.system = system
        self.regions = regions or []
        self.independent_candidates = np.asarray(
            independent_candidates if independent_candidates is not None
            else [False] * self.nparty, dtype=bool)
        if self.independent_candidates.shape != (self.nparty,):
            raise ValueError("Independent candidates must match the party list.")
        self.rng = rng if rng is not None else np.random.default_rng()
        self.danish = system["adjustment_preparation_method"] == "danish-regions"
        self.party_vote_info = party_vote_info
        self.party_votes = np.array(party_vote_info["votes"])
        source_votes = np.asarray(votes)
        self.party_stands_everywhere = np.all(source_votes > 0, axis=0)
        pruned_votes = pruned_votes if pruned_votes is not None else [0] * len(votes)
        self.pruned_votes = np.array(pruned_votes)
        if self.nconst == 1:
            self.pruned_votes = np.array([self.pruned_votes.sum()])
        else:
            assert len(self.pruned_votes) == self.nconst
        self.party_pruned_votes = party_vote_info.get("pruned", 0)
        minimums = [
            constituency["num_adj_seats"]
            for constituency in system["constituencies"]
        ]
        adjustment_seat_info = adjustment_seat_info or {
            "total": sum(minimums),
            "min_per_const": minimums,
            "max_per_const": minimums.copy(),
        }
        self.num_adjustment_seats = adjustment_seat_info["total"]
        self.min_adj_seats = np.asarray(
            adjustment_seat_info["min_per_const"], dtype=int)
        self.max_adj_seats = list(adjustment_seat_info["max_per_const"])
        if (len(self.min_adj_seats) != self.nconst
                or len(self.max_adj_seats) != self.nconst):
            raise ValueError(
                "Adjustment-seat bounds do not match the constituencies.")
        if (self.min_adj_seats < 0).any():
            raise ValueError("Adjustment-seat minimums must be non-negative.")
        if any(
                maximum is not None and maximum < minimum
                for minimum, maximum in zip(
                    self.min_adj_seats, self.max_adj_seats)):
            raise ValueError(
                "An adjustment-seat maximum is below its constituency minimum.")
        if self.num_adjustment_seats < int(self.min_adj_seats.sum()):
            raise ValueError(
                "Constituency minimums exceed the adjustment-seat total.")
        if (all(maximum is not None for maximum in self.max_adj_seats)
                and self.num_adjustment_seats > sum(self.max_adj_seats)):
            raise ValueError(
                "Constituency maxima are below the adjustment-seat total.")
        self.has_flexible_adj_seats = any(
            maximum is None or minimum < maximum
            for minimum, maximum in zip(
                self.min_adj_seats, self.max_adj_seats)
        )
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
        if party_votes is not None:
            self.party_votes = np.array(party_votes)
        if self.nconst == 1:
            self.votes = self.votes.sum(0)[None,:]
        else:
            assert len(self.votes) == self.nconst
        assert all(len(row) == self.nparty for row in self.votes)
        self.votesums = self.votes.sum(0)
        self.const_threshold_totals = self.votes.sum(1) + self.pruned_votes

    @staticmethod
    def display_seats(allSeats, adjSeats):
        if adjSeats > 0:
            return f"{allSeats} ({adjSeats})"
        elif allSeats > 0:
            return f"{allSeats}"
        else:
            return ""

    @staticmethod
    def display_decomposed_seats(all_seats, switching, adjustment):
        if all_seats or switching or adjustment:
            if not switching and not adjustment:
                return str(all_seats)
            return f"{all_seats} ({switching:+d}+{adjustment})"
        return ""

    def component_table(self, matrix):
        party_totals = matrix.sum(axis=0).tolist()
        rows = matrix.tolist() + [party_totals]
        if self.party_vote_info["specified"]:
            rows.extend([[0] * self.nparty, party_totals])
        return add_total_column(rows)

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
        preparation_method = self.system["adjustment_preparation_method"]
        swedish = preparation_method == "switching_se"
        if swedish:
            first_stage = self.component_table(
                self.switching_seat_changes)
            adjustment = self.component_table(
                self.adjustment_seat_allocations)
            for allrow, firstrow, adjustmentrow in zip(
                    self.results["all"], first_stage, adjustment):
                dispResult.append([
                    self.display_decomposed_seats(
                        total, first, added)
                    for total, first, added in zip(
                        allrow, firstrow, adjustmentrow)
                ])
        else:
            for allrow, adjrow in zip(
                    self.results["all"], self.results["adj"]):
                dispResult.append([
                    self.display_seats(total, adjustment)
                    for total, adjustment in zip(allrow, adjrow)
                ])
        
        return {
            "demo_tables":      self.demo_tables,
            "display_results":  dispResult
        }

    def assign_seats(self, use_thresholds=True):
        if self.danish:
            if not self.regions:
                raise ValueError("Danish allocation requires a region table and constituency regions.")
            if self.system["adjustment_method"] != "max-const-votes":
                raise ValueError("Danish regional preparation requires Maximum constituency votes.")
            if self.system.get_type("primary_divider") != "Division":
                raise ValueError("Danish fixed-seat allocation requires a divisor rule.")
            check_regions({
                "regions": self.regions,
                "constituencies": [dict(const, max_adj_seats=self.max_adj_seats[c])
                                   for c, const in enumerate(self.system["constituencies"])],
                "max_total_adj_seats": self.num_adjustment_seats,
                "party_vote_info": self.party_vote_info,
            })
            self.region_groups = danish.region_groups(self.system["constituencies"], self.regions)
        self.fixed_seats_alloc = []
        self.order = []
        self.fixed_row_sums = np.array([
            const["num_fixed_seats"]
            for const in self.system["constituencies"]
        ])
        self.desired_row_sums = np.array([
            const["num_fixed_seats"] + const["num_adj_seats"]
            for const in self.system["constituencies"]
        ])
        party_vote_info = self.party_vote_info
        self.use_thresholds = use_thresholds
        method_name = self.system["adjustment_method"]
        if (self.has_flexible_adj_seats
                and method_name not in FLEXIBLE_ADJUSTMENT_METHODS):
            raise ValueError(
                f'Adjustment-seat method "{method_name}" does not support '
                "constituency ranges; all adjustment-seat minimums and "
                "maximums must be equal.")
        self.total_const_seats = (
            int(self.fixed_row_sums.sum()) + self.num_adjustment_seats)
        self.set_national_votes()
        self.apportion_fixed_seats(use_thresholds)
        self.apportion_total_party_seats(use_thresholds)
        self.prepare_adjustment_seat_allocation()
        self.allocate_adjustment_seats()
        if party_vote_info["specified"]:
            self.add_national_adjustment_seats()
        else:
            self.results['all_grand_total'] = self.results['all_const_total']
        self.prepare_results()

    def set_national_votes(self):
        opt = self.system["seat_spec_options"]["party"]
        if opt == "totals":
            votes = self.votesums
            pruned_votes = self.pruned_votes.sum()
        elif opt == "party_vote_info":
            votes = self.party_votes
            pruned_votes = self.party_pruned_votes
        else:
            assert opt == "average"
            votes = (self.votesums + self.party_votes) / 2
            pruned_votes = (self.pruned_votes.sum() + self.party_pruned_votes) / 2
        self.nat_votes = votes
        self.nat_threshold_total = self.nat_votes.sum() + pruned_votes

    def apportion_fixed_seats(self, use_thresholds):
        constituencies = self.system["constituencies"]
        threshold = self.system["constituency_threshold"] if use_thresholds else 0
        national_or_constituency = (
            self.system["fixed_seat_eligibility"]
            == "national-or-constituency")
        if national_or_constituency:
            national_threshold = (
                self.system["adjustment_threshold"] if use_thresholds else 0)
            national_shares = (
                self.nat_votes / self.nat_threshold_total
                if self.nat_threshold_total else np.zeros_like(self.nat_votes)
            )
            nationally_eligible = national_shares * 100 >= national_threshold
        m_allocations = np.zeros((self.nconst, self.nparty), int)
        self.last = []
        self.results = {}
        for i in range(self.nconst):
            num_seats = constituencies[i]["num_fixed_seats"]
            if num_seats != 0:
                votes = self.votes[i]
                applied_threshold = threshold
                if national_or_constituency:
                    local_shares = (
                        votes / self.const_threshold_totals[i]
                        if self.const_threshold_totals[i] else np.zeros_like(votes)
                    )
                    eligible = nationally_eligible | (local_shares * 100 >= threshold)
                    votes = np.where(eligible, votes, 0)
                    applied_threshold = 0
                if self.danish:
                    eligible_votes = threshold_drop(
                        votes, [1, applied_threshold, 0, []],
                        threshold_total=self.const_threshold_totals[i])
                    alloc, last_in = danish.fixed_seats(
                        eligible_votes, num_seats, self.independent_candidates,
                        self.system.get_generator("primary_divider"), self.rng)
                else:
                    alloc, _, last_in = apportion1d_general(
                        v_votes=votes,
                        num_total_seats=num_seats,
                        prior_allocations=[],
                        rule=self.system.get_generator("primary_divider"),
                        type_of_rule=self.system.get_type("primary_divider"),
                        threshold_percent=applied_threshold,
                        threshold_total=self.const_threshold_totals[i],
                    )
                assert last_in  # last_in is not None because num_seats > 0
                self.last.append(last_in)
            else:
                alloc = np.zeros(self.nparty, int)
                self.last.append({'idx': None, 'active_votes': 0})
            m_allocations[i,:] = alloc

        v_allocations = m_allocations.sum(0)
        self.results["fixed_const_total"] = v_allocations

        if self.party_vote_info["specified"]:
            if self.system["nat_seats"]["num_fixed_seats"] > 0:
                nat_fixed_alloc, _, _ = apportion1d_general(
                    v_votes = self.nat_votes,
                    num_total_seats = self.system["nat_seats"]["num_fixed_seats"],
                    prior_allocations = [],
                    rule = self.system.get_generator("primary_divider"),
                    type_of_rule = self.system.get_type("primary_divider"),
                    threshold_percent = threshold,
                    threshold_total = self.nat_threshold_total,
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

        entitlement_votes = self.nat_votes
        norwegian = self.system["adjustment_method"] == "norwegian-law"
        if norwegian:
            # Positive votes in every source constituency are the simulator's
            # proxy for the Norwegian requirement to stand everywhere.
            entitlement_votes = np.where(
                self.party_stands_everywhere, self.nat_votes, 0)

        fixed_allocations = np.array(self.results["fixed_grand_total"])
        swedish = (
            self.system["adjustment_preparation_method"] == "switching_se")
        if self.danish:
            eligible = danish.eligible_parties(
                self.votes, self.results["fixed_const_seats"], self.independent_candidates,
                self.region_groups, self.const_threshold_totals, threshold, seats, choice)
            self.desired_col_sums = danish.party_totals(
                self.nat_votes, fixed_allocations, eligible, self.total_const_seats,
                self.system.get_generator("adj_determine_divider"),
                self.system.get_type("adj_determine_divider"), self.rng)
            self.adj_seat_gen = None
        elif swedish:
            national_shares = (
                self.nat_votes / self.nat_threshold_total
                if self.nat_threshold_total else np.zeros_like(self.nat_votes)
            )
            nationally_eligible = national_shares * 100 >= threshold
            protected_totals = np.where(
                nationally_eligible, 0, fixed_allocations)
            seats_for_national_allocation = (
                self.total_const_seats + nat_seats - int(protected_totals.sum()))
            if seats_for_national_allocation < 0:
                raise ValueError(
                    "Locally qualified Swedish seats exceed the total seat count.")
            national_votes = np.where(nationally_eligible, self.nat_votes, 0)
            if seats_for_national_allocation and not national_votes.any():
                raise ValueError("No party qualifies for Swedish national apportionment.")
            national_allocation, self.adj_seat_gen, _ = apportion1d_general(
                v_votes=national_votes,
                num_total_seats=seats_for_national_allocation,
                prior_allocations=[0] * len(self.nat_votes),
                rule=self.system.get_generator("adj_determine_divider"),
                type_of_rule=self.system.get_type("adj_determine_divider"),
            )
            self.desired_col_sums = np.asarray(
                national_allocation, dtype=int) + protected_totals
        else:
            if (norwegian
                and fixed_allocations.sum() < self.total_const_seats + nat_seats):
                qualified_votes = threshold_drop(
                    entitlement_votes,
                    [choice, threshold, seats, fixed_allocations],
                    threshold_total=self.nat_threshold_total,
                )
                if not any(qualified_votes):
                    raise ValueError(
                        "No party qualifies for Norwegian adjustment seats after "
                        "applying the threshold and everywhere-standing rule.")

            self.desired_col_sums, self.adj_seat_gen, _ = apportion1d_general(
                v_votes = entitlement_votes,
                num_total_seats = self.total_const_seats + nat_seats,
                prior_allocations = fixed_allocations,
                rule = self.system.get_generator("adj_determine_divider"),
                type_of_rule = self.system.get_type("adj_determine_divider"),
                threshold_percent = threshold,
                threshold_choice = choice,
                threshold_seats = seats,
                threshold_total = self.nat_threshold_total,
            )

        self.ref_seat_alloc, _, _ = apportion1d_general(
            v_votes=self.nat_votes,
            num_total_seats=self.total_const_seats + nat_seats,
            prior_allocations=[0] * len(self.nat_votes),
            rule=self.system.get_generator('adj_determine_divider'),
            type_of_rule=self.system.get_type('adj_determine_divider'),
        )
        total_votes = self.nat_votes.sum()
        self.fractional_party_seats = (
            self.nat_votes.astype(float) * (self.total_const_seats + nat_seats)
            / total_votes
            if total_votes else np.zeros(self.nparty)
        )

    def prepare_adjustment_seat_allocation(self):
        """Apply an optional operation before allocating adjustment seats."""
        method_name = self.system["adjustment_preparation_method"]
        fixed = np.asarray(self.results["fixed_const_seats"])
        self.preparation_stepbystep = None
        self.switching_seat_changes = np.zeros_like(fixed)
        if method_name == "none":
            self.prepared_const_seats = fixed.copy()
            return

        if self.danish:
            self.prepared_const_seats = fixed.copy()
            self.region_party_totals, self.preparation_stepbystep = danish.prepare_regions(
                self.votes, fixed, self.desired_col_sums, self.regions, self.region_groups,
                self.system.get_generator("adj_preparation_divider"), self.rng)
            return

        method = ADJUSTMENT_PREPARATION_METHODS[method_name]
        preparation_gen = self.system.get_generator("adj_preparation_divider")
        self.prepared_const_seats, self.preparation_stepbystep = method(
            self.votes,
            self.fixed_row_sums,
            self.desired_col_sums,
            fixed,
            preparation_gen,
            nat_votes=self.nat_votes,
            nat_threshold_total=self.nat_threshold_total,
            const_threshold_totals=self.const_threshold_totals,
            national_threshold=(
                self.system["adjustment_threshold"] if self.use_thresholds else 0),
            local_threshold=(
                self.system["constituency_threshold"] if self.use_thresholds else 0),
            total_seats=self.total_const_seats,
        )
        if "party_totals" in self.preparation_stepbystep:
            self.desired_col_sums = np.asarray(
                self.preparation_stepbystep["party_totals"], dtype=int)
        self.switching_seat_changes = np.asarray(
            self.preparation_stepbystep.get(
                "seat_changes", np.zeros_like(self.prepared_const_seats)),
            dtype=int,
        )

    def allocate_adjustment_seats(self):
        """Allocate adjustment seats to constituency lists."""
        method_name = self.system["adjustment_method"]
        self.gen = self.system.get_generator("adj_alloc_divider")
        stepbystep = None
        method = ADJUSTMENT_METHODS[method_name]
        consts = self.system["constituencies"]
        fixed_seats = [con["num_fixed_seats"] for con in consts]
        if self.danish:
            all_const_seats, stepbystep = danish.allocate_regions(
                self.votes, self.prepared_const_seats, self.region_party_totals,
                self.regions, self.region_groups, self.min_adj_seats, self.max_adj_seats,
                self.gen, self.rng)
        else:
            all_const_seats, stepbystep = method(
                self.votes,
                self.desired_row_sums,
                self.desired_col_sums,
                self.prepared_const_seats,
                self.gen,
                adj_seat_gen=self.adj_seat_gen,
                v_fixed_seats=fixed_seats,
                last=self.last,
                nat_prior_allocations=(self.results['fixed_nat_seats']
                    if self.party_vote_info['specified'] else None),
                num_adjustment_seats=self.num_adjustment_seats,
                min_adj_seats=self.min_adj_seats,
                max_adj_seats=self.max_adj_seats,
            )

        adjustment_row_totals = (
            np.asarray(all_const_seats).sum(axis=1) - self.fixed_row_sums)
        if int(adjustment_row_totals.sum()) != self.num_adjustment_seats:
            raise RuntimeError(
                "Adjustment-seat allocation returned the wrong total.")
        if (adjustment_row_totals < self.min_adj_seats).any() or any(
                maximum is not None and adjustment_row_totals[index] > maximum
                for index, maximum in enumerate(self.max_adj_seats)):
            raise RuntimeError(
                "Adjustment-seat allocation violated constituency bounds.")

        self.adjustment_seat_allocations = (
            np.asarray(all_const_seats) - self.prepared_const_seats)
        if self.system["adjustment_preparation_method"] == "none":
            adj_const_seats = all_const_seats - self.results["fixed_const_seats"]
        else:
            adj_const_seats = self.adjustment_seat_allocations
        self.results["all_const_seats"] = all_const_seats
        self.results["adj_const_seats"] = adj_const_seats
        self.results["adj_const_total"] = adj_const_seats.sum(0)
        self.results["all_const_total"] = all_const_seats.sum(0)
        self.final_row_sums = all_const_seats.sum(1)
        self.demo_tables = []
        demo_stages = []
        if self.preparation_stepbystep:
            demo_stages.append((
                self.preparation_stepbystep,
                ADJUSTMENT_PREPARATION_DEMO_TABLE_FORMATS[
                    self.system["adjustment_preparation_method"]],
            ))
        if stepbystep:
            formats = stepbystep.get("format", DEMO_TABLE_FORMATS[method_name])
            functions = stepbystep.get("functions")
            if functions is None:
                functions = [stepbystep["function"]]
            if len(functions) == 1:
                formats = [formats]
            demo_stages.extend(
                ({"data": stepbystep["data"], "function": function}, formats[i])
                for i, function in enumerate(functions)
            )
        for demo, format in demo_stages:
            if demo["data"]:
                headers, steps, sup_header = demo["function"](
                    self.system, demo["data"])
                demo_table = {
                    "headers":    headers,
                    "steps":      steps,
                    "sup_header": sup_header,
                    "format":     format,
                }
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
        """Calculate threshold-free fractional seat shares for quality measures."""
        col_sums = np.array(self.fractional_party_seats)
        row_sums = np.array(self.final_row_sums)
        total_votes = self.votes.sum()
        ref_seat_shares = (
            self.votes.astype(float) * self.total_const_seats / total_votes
            if total_votes else np.zeros_like(self.votes, dtype=float)
        )
        row_constraints = scaling in {"both", "const"}
        col_constraints = scaling in {"both", "party"}
        error = 1e-8
        if row_constraints and col_constraints:
            equal_margins = np.isclose(row_sums.sum(), col_sums.sum())
            for _ in range(10000):
                current_rows = ref_seat_shares.sum(axis=1)
                ref_seat_shares *= np.divide(
                    row_sums,
                    current_rows,
                    out=np.ones_like(row_sums, dtype=float),
                    where=current_rows != 0,
                )[:, None]

                current_cols = ref_seat_shares.sum(axis=0)
                if equal_margins:
                    ref_seat_shares *= np.divide(
                        col_sums,
                        current_cols,
                        out=np.ones_like(col_sums, dtype=float),
                        where=current_cols != 0,
                    )[None, :]
                    if np.max(np.abs(
                            ref_seat_shares.sum(axis=1) - row_sums)) <= error:
                        break
                else:
                    over = current_cols > col_sums + error
                    if not over.any():
                        break

                    for p in np.flatnonzero(over):
                        ref_seat_shares[:, p] *= col_sums[p] / current_cols[p]

                    under = ~over
                    available = self.total_const_seats - col_sums[over].sum()
                    current = ref_seat_shares[:, under].sum()
                    if current:
                        ref_seat_shares[:, under] *= available / current
            else:
                raise RuntimeError(
                    'Reference seat share scaling did not converge. This may '
                    'happen when isolated parties or constituencies, such as '
                    'Åland, make party and constituency totals incompatible. '
                    'Try "within constituencies" scaling.'
                )
        elif row_constraints:
            for c, row_sum in enumerate(row_sums):
                current = ref_seat_shares[c, :].sum()
                if current:
                    ref_seat_shares[c, :] *= row_sum / current
        elif col_constraints:
            for p, col_sum in enumerate(col_sums):
                current = ref_seat_shares[:, p].sum()
                if current:
                    ref_seat_shares[:, p] *= col_sum / current

        self.ref_seat_shares = ref_seat_shares
        self.total_ref_const = self.ref_seat_shares.sum(0)
        self.total_ref_seat_shares = self.fractional_party_seats.copy()
        if self.party_vote_info['specified']:
            self.total_ref_nat = self.total_ref_seat_shares - self.total_ref_const
            self.total_ref_nat[np.abs(self.total_ref_nat) < error] = 0
        else:
            self.total_ref_nat = np.zeros(self.nparty)
