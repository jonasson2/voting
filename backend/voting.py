# coding:utf-8
"""
This module contains the core voting system logic.
"""

from table_util import add_total_column
from apportion import apportion1d_general, threshold_drop
from dictionaries import ADJUSTMENT_METHODS
from dictionaries import FLEXIBLE_ADJUSTMENT_METHODS
from dictionaries import REGIONAL_ADJUSTMENT_METHODS
from dictionaries import DEMO_TABLE_FORMATS
from entropy_score import calculate as calculate_entropy_score
from entropy_score import is_available as entropy_score_is_available
import numpy as np
from methods import danish, regional
from methods.switching_se import switching as apply_swedish_rules
from ties import TieReport
from vote_table import check_regions


REFERENCE_SCALING_TOLERANCE = 1e-8


def _scale_to_rows(matrix, row_sums):
    current = matrix.sum(axis=1)
    factors = np.divide(
        row_sums, current, out=np.ones_like(row_sums, dtype=float),
        where=current != 0)
    matrix *= factors[:, None]


def _scale_to_columns(matrix, column_sums):
    current = matrix.sum(axis=0)
    factors = np.divide(
        column_sums, current, out=np.ones_like(column_sums, dtype=float),
        where=current != 0)
    matrix *= factors[None, :]


def _scale_to_both_margins(matrix, row_sums, column_sums, total_seats):
    equal_margins = np.isclose(row_sums.sum(), column_sums.sum())
    for _ in range(10000):
        _scale_to_rows(matrix, row_sums)
        current_columns = matrix.sum(axis=0)
        if equal_margins:
            _scale_to_columns(matrix, column_sums)
            row_error = np.max(np.abs(matrix.sum(axis=1) - row_sums))
            if row_error <= REFERENCE_SCALING_TOLERANCE:
                return
            continue

        over = current_columns > column_sums + REFERENCE_SCALING_TOLERANCE
        if not over.any():
            return
        for party in np.flatnonzero(over):
            matrix[:, party] *= column_sums[party] / current_columns[party]
        available = total_seats - column_sums[over].sum()
        current = matrix[:, ~over].sum()
        if current:
            matrix[:, ~over] *= available / current
    raise RuntimeError(
        'Reference seat share scaling did not converge. This may happen when '
        'isolated parties or constituencies, such as Åland, make party and '
        'constituency totals incompatible. Try "within constituencies" scaling.'
    )


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
        self.rng = rng
        self.tie_report = TieReport()
        self.has_regions = bool(self.regions)
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
        self._set_adjustment_seat_bounds(adjustment_seat_info)
        self.set_votes(votes)
        self.reference_results = []
        self.vote_table_name = vote_table_name

    def _set_adjustment_seat_bounds(self, adjustment_seat_info):
        """Normalize and validate the adjustment-seat total and bounds."""
        minimums = [
            constituency["num_adj_seats"]
            for constituency in self.system["constituencies"]
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

    def entropy_score_available(self):
        return entropy_score_is_available(self)

    def entropy_score(self, optimum_cache=None):
        return calculate_entropy_score(self, optimum_cache)

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
    def display_swedish_seats(all_seats, adjustment, switched):
        display = Election.display_seats(all_seats, adjustment)
        return f"{display or all_seats}*" if switched else display

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

    def get_result_excel(self, entropy_cache=None):
        return {
            "vote_table_name": self.vote_table_name,
            "system": self.system,
            "results": self.results,
            "demo_tables": self.demo_tables,
            "entropy_score": self.entropy_score(entropy_cache),
        }

    def get_result_web(self):
        dispResult = []
        swedish = self.system["special_rules"] == "swedish"
        if swedish:
            adjustment = self.component_table(
                self.adjustment_seat_allocations)
            switched = self.switching_seat_changes != 0
            for row_index, (allrow, adjustmentrow) in enumerate(zip(
                    self.results["all"], adjustment)):
                dispResult.append([
                    self.display_swedish_seats(
                        total, added,
                        row_index < self.nconst and party_index < self.nparty
                        and switched[row_index, party_index])
                    for party_index, (total, added) in enumerate(zip(
                        allrow, adjustmentrow))
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
            "ties":             self.tie_report.events,
            "switching_affected": bool(switched.any()) if swedish else False,
            "display_results":  dispResult
        }

    def report_ties(self, stage, labels=None):
        if self.rng is not None:
            return None
        if labels is None:
            labels = [f'{const["name"]}: {party}'
                      for const in self.system["constituencies"]
                      for party in self.system["parties"]]
        return self.tie_report.reporter(stage, labels)

    def _prepare_regional_allocation(self):
        if not self.has_regions:
            return
        if self.system.get_type("primary_divider") != "Division":
            raise ValueError(
                "Regional fixed-seat allocation requires a divisor rule.")
        check_regions({
            "regions": self.regions,
            "constituencies": [
                dict(constituency, max_adj_seats=self.max_adj_seats[index])
                for index, constituency in enumerate(
                    self.system["constituencies"])
            ],
            "max_total_adj_seats": self.num_adjustment_seats,
            "party_vote_info": self.party_vote_info,
        })
        self.region_groups = regional.region_groups(
            self.system["constituencies"], self.regions)

    def _initialize_seat_allocation(self, use_thresholds):
        self.tie_report = TieReport()
        if self.system["special_rules"] == "danish" and not self.has_regions:
            raise ValueError(
                "Danish regional allocation requires a region table.")
        self._prepare_regional_allocation()
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
        self.use_thresholds = use_thresholds

    def _validate_adjustment_method(self):
        method_name = self.system["adjustment_method"]
        if (self.num_adjustment_seats > int(self.min_adj_seats.sum())
                and method_name not in FLEXIBLE_ADJUSTMENT_METHODS):
            raise ValueError(
                f'Adjustment-seat method "{method_name}" does not support '
                "constituency ranges with a remaining seat pool; it requires "
                "a predetermined final seat count in each constituency. "
                "Use Maximum constituency votes or Maximum constituency vote percentage.")

    def assign_seats(self, use_thresholds=True):
        self._initialize_seat_allocation(use_thresholds)
        self._validate_adjustment_method()
        self.total_const_seats = (
            int(self.fixed_row_sums.sum()) + self.num_adjustment_seats)
        self.set_national_votes()
        self.apportion_fixed_seats(use_thresholds)
        self.apportion_total_party_seats(use_thresholds)
        self.apply_special_rules_and_regional_allocation()
        self.allocate_adjustment_seats()
        if self.party_vote_info["specified"]:
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

    def _fixed_seat_votes(self, index, nationally_eligible, local_threshold):
        votes = self.votes[index]
        local_total = self.const_threshold_totals[index]
        local_shares = (
            votes / local_total if local_total else np.zeros_like(votes))
        locally_eligible = local_shares * 100 >= local_threshold
        if self.system["fixed_seat_threshold_choice"]:
            eligible = nationally_eligible | locally_eligible
        else:
            eligible = nationally_eligible & locally_eligible
        return np.where(eligible, votes, 0)

    def _allocate_fixed_constituency(
            self, index, nationally_eligible, local_threshold):
        constituency = self.system["constituencies"][index]
        num_seats = constituency["num_fixed_seats"]
        if num_seats == 0:
            return (np.zeros(self.nparty, int),
                    {'idx': None, 'active_votes': 0})

        on_tie = self.report_ties(
            f'Fixed seats in {constituency["name"]}', self.system["parties"])
        votes = self._fixed_seat_votes(
            index, nationally_eligible, local_threshold)
        if self.system["special_rules"] == "danish":
            eligible_votes = threshold_drop(
                votes, [1, 0, 0, []],
                threshold_total=self.const_threshold_totals[index])
            allocation, last = danish.fixed_seats(
                eligible_votes, num_seats, self.independent_candidates,
                self.system.get_generator("primary_divider"), self.rng, on_tie)
        else:
            max_seats = (
                np.where(self.independent_candidates, 1, num_seats)
                if self.independent_candidates.any() else None)
            allocation, _, last = apportion1d_general(
                v_votes=votes,
                num_total_seats=num_seats,
                prior_allocations=[],
                rule=self.system.get_generator("primary_divider"),
                type_of_rule=self.system.get_type("primary_divider"),
                threshold_percent=0,
                threshold_total=self.const_threshold_totals[index],
                on_tie=on_tie,
                max_seats=max_seats,
            )
        assert last is not None
        return allocation, last

    def _allocate_national_fixed_seats(self, local_threshold):
        if not self.party_vote_info["specified"]:
            return None
        num_seats = self.system["nat_seats"]["num_fixed_seats"]
        if num_seats == 0:
            return np.zeros(len(self.party_votes), int)
        allocation, _, _ = apportion1d_general(
            v_votes=self.nat_votes,
            num_total_seats=num_seats,
            prior_allocations=[],
            rule=self.system.get_generator("primary_divider"),
            type_of_rule=self.system.get_type("primary_divider"),
            threshold_percent=local_threshold,
            threshold_total=self.nat_threshold_total,
            on_tie=self.report_ties(
                "National fixed seats", self.system["parties"]),
            eligible=(~self.independent_candidates
                      if self.independent_candidates.any() else None),
        )
        return np.asarray(allocation)

    def apportion_fixed_seats(self, use_thresholds):
        local_threshold = (
            self.system["constituency_threshold"] if use_thresholds else 0)
        national_threshold = (
            self.system["fixed_seat_national_threshold"] if use_thresholds else 0)
        national_shares = (
            self.nat_votes / self.nat_threshold_total
            if self.nat_threshold_total else np.zeros_like(self.nat_votes)
        )
        nationally_eligible = national_shares * 100 >= national_threshold
        m_allocations = np.zeros((self.nconst, self.nparty), int)
        self.last = []
        self.results = {}
        for i in range(self.nconst):
            allocation, last = self._allocate_fixed_constituency(
                i, nationally_eligible, local_threshold)
            m_allocations[i, :] = allocation
            self.last.append(last)

        v_allocations = m_allocations.sum(0)
        self.results["fixed_const_total"] = v_allocations
        national_allocation = self._allocate_national_fixed_seats(local_threshold)
        if national_allocation is not None:
            v_allocations += national_allocation
            self.results["fixed_nat_seats"] = national_allocation
        self.results["fixed_const_seats"] = m_allocations
        self.results["fixed_grand_total"] = v_allocations

    def _standing_eligible(self):
        standing_required = self.system["require_votes_in_all_constituencies"]
        standing = (
            self.party_stands_everywhere if standing_required
            else np.ones(self.nparty, dtype=bool))
        return standing & ~self.independent_candidates

    def _apportion_danish_party_totals(
            self, fixed, threshold, threshold_seats, threshold_choice,
            standing_eligible, use_thresholds, on_tie):
        eligible = danish.eligible_parties(
            self.votes, self.results["fixed_const_seats"],
            self.independent_candidates, self.region_groups,
            self.const_threshold_totals, threshold, threshold_seats,
            threshold_choice, use_thresholds)
        eligible &= standing_eligible
        args = (
            self.nat_votes,
            fixed,
            eligible,
            self.total_const_seats,
            self.system.get_generator("adj_determine_divider"),
            self.system.get_type("adj_determine_divider"),
        )
        totals = danish.party_totals(*args, self.rng, on_tie)
        return totals, None

    def _apportion_swedish_party_totals(
            self, fixed, threshold, standing_eligible, total_seats, on_tie):
        national_shares = (
            self.nat_votes / self.nat_threshold_total
            if self.nat_threshold_total else np.zeros_like(self.nat_votes))
        nationally_eligible = (
            national_shares * 100 >= threshold) & standing_eligible
        protected_totals = np.where(nationally_eligible, 0, fixed)
        seats_to_allocate = total_seats - int(protected_totals.sum())
        if seats_to_allocate < 0:
            raise ValueError(
                "Locally qualified Swedish seats exceed the total seat count.")
        national_votes = np.where(nationally_eligible, self.nat_votes, 0)
        if seats_to_allocate and not national_votes.any():
            raise ValueError(
                "No party qualifies for Swedish national apportionment.")
        allocation, seat_generator, _ = apportion1d_general(
            v_votes=national_votes,
            num_total_seats=seats_to_allocate,
            prior_allocations=[0] * len(self.nat_votes),
            rule=self.system.get_generator("adj_determine_divider"),
            type_of_rule=self.system.get_type("adj_determine_divider"),
            on_tie=on_tie,
        )
        return np.asarray(allocation, dtype=int) + protected_totals, seat_generator

    def _apportion_default_party_totals(
            self, fixed, threshold, threshold_seats, threshold_choice,
            standing_eligible, total_seats, on_tie):
        allocation, seat_generator, _ = apportion1d_general(
            v_votes=self.nat_votes,
            num_total_seats=total_seats,
            prior_allocations=fixed,
            rule=self.system.get_generator("adj_determine_divider"),
            type_of_rule=self.system.get_type("adj_determine_divider"),
            threshold_percent=threshold,
            threshold_choice=threshold_choice,
            threshold_seats=threshold_seats,
            threshold_total=self.nat_threshold_total,
            on_tie=on_tie,
            eligible=standing_eligible,
        )
        return allocation, seat_generator

    def _calculate_reference_party_seats(self, total_seats):
        self.ref_seat_alloc, _, _ = apportion1d_general(
            v_votes=self.nat_votes,
            num_total_seats=total_seats,
            prior_allocations=[0] * len(self.nat_votes),
            rule=self.system.get_generator('adj_determine_divider'),
            type_of_rule=self.system.get_type('adj_determine_divider'),
        )
        total_votes = self.nat_votes.sum()
        self.fractional_party_seats = (
            self.nat_votes.astype(float) * total_seats / total_votes
            if total_votes else np.zeros(self.nparty)
        )

    def apportion_total_party_seats(self, use_thresholds):
        """Calculate the total number of seats assigned to each party."""
        national_seats = (
            self.system["nat_seats"]["num_fixed_seats"]
            + self.system["nat_seats"]["num_adj_seats"]
            if self.party_vote_info["specified"] else 0)
        total_seats = self.total_const_seats + national_seats
        threshold = (
            self.system["adjustment_threshold"] if use_thresholds else 0)
        threshold_choice = (
            self.system["adj_threshold_choice"] if use_thresholds else 0)
        threshold_seats = (
            self.system["adjustment_threshold_seats"] if use_thresholds else 0)
        standing_eligible = self._standing_eligible()
        fixed = np.asarray(self.results["fixed_grand_total"])
        on_tie = self.report_ties("Party totals", self.system["parties"])

        special_rules = self.system["special_rules"]
        if special_rules == "danish":
            result = self._apportion_danish_party_totals(
                fixed, threshold, threshold_seats, threshold_choice,
                standing_eligible, use_thresholds, on_tie)
        elif special_rules == "swedish":
            result = self._apportion_swedish_party_totals(
                fixed, threshold, standing_eligible, total_seats, on_tie)
        else:
            result = self._apportion_default_party_totals(
                fixed, threshold, threshold_seats, threshold_choice,
                standing_eligible, total_seats, on_tie)
        self.desired_col_sums, self.adj_seat_gen = result
        self._calculate_reference_party_seats(total_seats)

    def apply_special_rules_and_regional_allocation(self):
        """Apply Swedish switching and any regional allocation stage."""
        fixed = np.asarray(self.results["fixed_const_seats"])
        self.special_rules_stepbystep = None
        self.regional_stepbystep = None
        self.switching_seat_changes = np.zeros_like(fixed)
        self.prepared_const_seats = fixed.copy()
        self._apply_swedish_switching(fixed)
        self._allocate_to_regions()

    def _apply_swedish_switching(self, fixed):
        if self.system["special_rules"] != "swedish":
            return
        self.prepared_const_seats, self.special_rules_stepbystep = (
            apply_swedish_rules(
                self.votes,
                self.fixed_row_sums,
                self.desired_col_sums,
                fixed,
                self.system.get_generator("adj_determine_divider"),
                nat_votes=self.nat_votes,
                nat_threshold_total=self.nat_threshold_total,
                const_threshold_totals=self.const_threshold_totals,
                national_threshold=(
                    self.system["adjustment_threshold"] if self.use_thresholds else 0),
                local_threshold=(
                    self.system["constituency_threshold"] if self.use_thresholds else 0),
                total_seats=self.total_const_seats,
                rng=self.rng,
                on_tie=self.report_ties("Swedish switching"),
            )
        )
        if "party_totals" in self.special_rules_stepbystep:
            self.desired_col_sums = np.asarray(
                self.special_rules_stepbystep["party_totals"], dtype=int)
        self.switching_seat_changes = np.asarray(
            self.special_rules_stepbystep.get(
                "seat_changes", np.zeros_like(self.prepared_const_seats)),
            dtype=int,
        )

    def _allocate_to_regions(self):
        if not self.has_regions:
            return
        regional_method_name = self.system["regional_adjustment_method"]
        on_tie = None
        if self.rng is None:
            on_tie = self.report_ties("Regional adjustment seats", [
                f'{region["abbreviation"]}: {party}'
                for region in self.regions
                for party in self.system["parties"]
            ])
        self.region_party_totals, self.regional_stepbystep = (
            regional.allocate_to_regions(
                self.votes,
                self.prepared_const_seats,
                self.desired_col_sums,
                self.regions,
                self.region_groups,
                self.system.get_generator("regional_adjustment_divider"),
                self.rng,
                on_tie,
                method=REGIONAL_ADJUSTMENT_METHODS[regional_method_name],
                method_name=regional_method_name,
            )
        )

    def _run_adjustment_method(self):
        method_name = self.system["adjustment_method"]
        self.gen = self.system.get_generator("adj_alloc_divider")
        method = ADJUSTMENT_METHODS[method_name]
        consts = self.system["constituencies"]
        fixed_seats = [con["num_fixed_seats"] for con in consts]
        if self.has_regions:
            return regional.allocate_within_regions(
                self.votes, self.prepared_const_seats, self.region_party_totals,
                self.regions, self.region_groups, self.min_adj_seats, self.max_adj_seats,
                self.gen, self.rng, self.report_ties("Adjustment seats"),
                method=method, method_name=method_name)
        return method(
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
            rng=self.rng,
            on_tie=self.report_ties("Adjustment seats"),
            on_party_tie=self.report_ties(
                "Adjustment-seat party order", self.system["parties"]),
        )

    def _validate_adjustment_allocation(self, all_const_seats):
        adjustment_row_totals = (
            all_const_seats.sum(axis=1) - self.fixed_row_sums)
        if int(adjustment_row_totals.sum()) != self.num_adjustment_seats:
            raise RuntimeError(
                "Adjustment-seat allocation returned the wrong total.")
        if (adjustment_row_totals < self.min_adj_seats).any() or any(
                maximum is not None and adjustment_row_totals[index] > maximum
                for index, maximum in enumerate(self.max_adj_seats)):
            raise RuntimeError(
                "Adjustment-seat allocation violated constituency bounds.")

    def _record_adjustment_results(self, all_const_seats):
        self.adjustment_seat_allocations = all_const_seats - self.prepared_const_seats
        if self.system["special_rules"] == "swedish":
            adj_const_seats = self.adjustment_seat_allocations
        else:
            adj_const_seats = all_const_seats - self.results["fixed_const_seats"]
        self.results["all_const_seats"] = all_const_seats
        self.results["adj_const_seats"] = adj_const_seats
        self.results["adj_const_total"] = adj_const_seats.sum(0)
        self.results["all_const_total"] = all_const_seats.sum(0)
        self.final_row_sums = all_const_seats.sum(1)

    def _demo_stages(self, stepbystep):
        demo_stages = []

        def append_demo(demo, default_formats, title_prefix=None):
            formats = demo.get("format", default_formats)
            functions = demo.get("functions")
            if functions is None:
                functions = [demo["function"]]
            if len(functions) == 1:
                formats = [formats]
            demo_stages.extend((
                {
                    "data": demo["data"],
                    "function": function,
                    "title_prefix": title_prefix,
                    "constituencies": demo.get("constituencies"),
                    "scope": demo.get("scope"),
                },
                formats[index],
            ) for index, function in enumerate(functions))

        if self.special_rules_stepbystep:
            append_demo(
                self.special_rules_stepbystep,
                "clss33")
        if self.regional_stepbystep:
            append_demo(
                self.regional_stepbystep,
                DEMO_TABLE_FORMATS[self.system["regional_adjustment_method"]])
        if stepbystep:
            method_name = self.system["adjustment_method"]
            default_formats = DEMO_TABLE_FORMATS[method_name]
            if "stages" in stepbystep:
                for stage in stepbystep["stages"]:
                    append_demo(
                        stage["demo"], default_formats,
                        stage.get("title_prefix"))
            else:
                append_demo(stepbystep, default_formats)
        return demo_stages

    def _build_demo_tables(self, stepbystep):
        self.demo_tables = []
        for demo, table_format in self._demo_stages(stepbystep):
            if demo["data"]:
                demo_system = self.system
                if demo.get("constituencies") is not None:
                    demo_system = dict(
                        self.system,
                        constituencies=demo["constituencies"],
                    )
                headers, steps, sup_header = demo["function"](
                    demo_system, demo["data"])
                if demo.get("scope") == "region":
                    headers = [
                        heading.replace("Constituency", "Region").replace(
                            "constituency", "region")
                        for heading in headers
                    ]
                    if sup_header:
                        sup_header = sup_header.replace(
                            "Constituency", "Region").replace(
                                "constituency", "region")
                if demo.get("title_prefix"):
                    sup_header = (
                        f'{demo["title_prefix"]}: {sup_header}'
                        if sup_header else demo["title_prefix"])
                self.demo_tables.append({
                    "headers":    headers,
                    "steps":      steps,
                    "sup_header": sup_header,
                    "format":     table_format,
                })
        self.fix_special_formats()

    def allocate_adjustment_seats(self):
        """Allocate adjustment seats to constituency lists."""
        all_const_seats, stepbystep = self._run_adjustment_method()
        all_const_seats = np.asarray(all_const_seats)
        self._validate_adjustment_allocation(all_const_seats)
        self._record_adjustment_results(all_const_seats)
        self._build_demo_tables(stepbystep)

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
        if row_constraints and col_constraints:
            _scale_to_both_margins(
                ref_seat_shares, row_sums, col_sums, self.total_const_seats)
        elif row_constraints:
            _scale_to_rows(ref_seat_shares, row_sums)
        elif col_constraints:
            _scale_to_columns(ref_seat_shares, col_sums)

        self.ref_seat_shares = ref_seat_shares
        self.total_ref_const = self.ref_seat_shares.sum(0)
        self.total_ref_seat_shares = self.fractional_party_seats.copy()
        if self.party_vote_info['specified']:
            self.total_ref_nat = self.total_ref_seat_shares - self.total_ref_const
            self.total_ref_nat[
                np.abs(self.total_ref_nat) < REFERENCE_SCALING_TOLERANCE] = 0
        else:
            self.total_ref_nat = np.zeros(self.nparty)
