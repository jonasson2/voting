"""Vote perturbation and seat-displacement helpers for sensitivity analysis."""

import numpy as np

from generate_votes import generate_votes


SENSITIVITY_CHANGE_GROUPS = (
    ("sensitivityListOnlyChange", "sensitivity_list_only_change",
     "List allocations change;\nparty totals unchanged"),
    ("sensitivityPartyChange", "sensitivity_party_change",
     "Party totals change"),
)
SENSITIVITY_PERCENT_MEASURES = {measure for _, measure, _ in SENSITIVITY_CHANGE_GROUPS}


def sensitivity_statistics(outer, perturbations):
    """Separate individual displacement spread from uncertainty of its mean.

    With M outer elections and S perturbations each, the variance of the
    outer means estimates A + B/S, where A is between-election variance and
    B is mean conditional variance. Individual displacement variance is A+B.
    For one outer election, report conditional spread and uncertainty only.
    Both accumulators can be merged before applying these formulas.
    """
    result = {
        "avg": outer.mean(),
        "min": perturbations.minimum(),
        "max": perturbations.maximum(),
    }
    if perturbations.n < 2:
        for key in ("std", "se", "lo95", "hi95"):
            result[key] = np.full(outer.shape, None).tolist()
        return result

    count = outer.n
    inner_count = perturbations.n // count
    within_variance = (
        np.maximum(0, perturbations.M2 - inner_count * outer.M2)
        / (count * (inner_count - 1))
        if inner_count > 1 else np.zeros(outer.shape))
    if count > 1:
        means_variance = outer.M2 / (count - 1)
        variance = means_variance + (1 - 1 / inner_count) * within_variance
        mean_variance = means_variance / count
    else:
        variance = within_variance
        mean_variance = within_variance / inner_count
    se = np.sqrt(mean_variance)
    result.update(
        std=np.sqrt(variance).tolist(),
        se=se.tolist(),
        lo95=(outer.M1 - 1.96 * se).tolist(),
        hi95=(outer.M1 + 1.96 * se).tolist(),
    )
    return result


def sensitivity_covs(percentages):
    """Validate percentages and return ascending CoVs as fractions."""
    if not isinstance(percentages, list) or not percentages:
        raise ValueError("Specify at least one sensitivity CoV.")
    try:
        values = [float(value) for value in percentages]
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Sensitivity CoVs must be positive numbers.") from error
    if any(not np.isfinite(value) or value <= 0 for value in values):
        raise ValueError("Sensitivity CoVs must be positive numbers.")
    if len(set(values)) != len(values):
        raise ValueError("Sensitivity CoVs must be distinct.")
    return [value / 100 for value in sorted(values)]


def _normalize_vote_batches(generated, reference):
    """Preserve every reference row total in every generated vote table."""
    generated = np.asarray(generated, dtype=float)
    reference = np.asarray(reference, dtype=float)
    reference_totals = reference.sum(axis=-1)
    generated_totals = generated.sum(axis=-1)
    if np.any((generated_totals == 0) & (reference_totals != 0)):
        raise ValueError("Perturbed votes cannot be normalized from zero.")
    factors = np.divide(
        reference_totals,
        generated_totals,
        out=np.zeros_like(generated_totals),
        where=generated_totals != 0,
    )
    return generated * factors[..., None]


def generate_perturbations(
        votes, party_votes, count, cov, distribution, rng):
    """Generate minor vote tables around one major simulated election."""
    votes = np.asarray(votes, dtype=float)
    vote_bases = np.broadcast_to(votes, (count,) + votes.shape)
    generated_votes = generate_votes(vote_bases, cov, distribution, rng)
    generated_votes = _normalize_vote_batches(generated_votes, votes)

    generated_party_votes = None
    if party_votes is not None:
        party_votes = np.asarray(party_votes, dtype=float)
        party_bases = np.broadcast_to(
            party_votes, (count, 1, len(party_votes)))
        generated_party_votes = generate_votes(
            party_bases, cov, distribution, rng)
        generated_party_votes = _normalize_vote_batches(
            generated_party_votes, party_votes[None, :])[:, 0, :]

    return generated_votes, generated_party_votes


def seat_displacements(base_elections, perturbed_elections):
    """Return between-party and within-party list displacement by system."""
    between_parties = []
    within_parties = []
    for base, perturbed in zip(base_elections, perturbed_elections):
        base_lists = np.asarray(base.results["all_const_seats"])
        perturbed_lists = np.asarray(perturbed.results["all_const_seats"])
        if base.party_vote_info["specified"]:
            base_lists = np.vstack((
                base_lists, np.asarray(base.results["all_nat_seats"])))
            perturbed_lists = np.vstack((
                perturbed_lists,
                np.asarray(perturbed.results["all_nat_seats"])))

        overall = np.abs(perturbed_lists - base_lists).sum() / 2
        party = np.abs(
            np.asarray(perturbed.results["all_grand_total"])
            - np.asarray(base.results["all_grand_total"])
        ).sum() / 2
        within = overall - party
        if within < -1e-10:
            raise RuntimeError(
                "Internal error: party displacement exceeds list displacement.")
        between_parties.append(float(party))
        within_parties.append(float(max(0, within)))
    return np.asarray(between_parties), np.asarray(within_parties)


SINGLE_LIST_GROUPS = (
    ("singleListNoChange", "single_list_no_change", "No seat changes",
     "Entire allocation unchanged."),
    ("singleListOtherParties", "single_list_other_parties", "Changes confined to other parties",
     "Some seats change, but no list of the selected party changes. All party totals remain unchanged."),
    ("singleListOtherLists", "single_list_other_lists", "Changes to other lists\nof selected party",
     "Other lists of the selected party change, but the selected list does not. Other parties may also change. All party totals remain unchanged."),
    ("singleListSelected", "single_list_selected", "Changes to selected list",
     "The selected list's seat count changes; other lists may also change. All party totals remain unchanged."),
    ("singleListPartyTotals", "single_list_party_totals", "Party totals change",
     "At least one party's total changes, regardless of which lists change."),
)
SINGLE_LIST_MEASURES = [measure for _, measure, _, _ in SINGLE_LIST_GROUPS]
SENSITIVITY_PERCENT_MEASURES.update(SINGLE_LIST_MEASURES)


def single_list_perturbations(votes, count, cov, distribution, rng):
    """Choose a party, then one of its positive-vote constituency lists uniformly.

    Zero-vote cells are treated as absent lists. National party votes are not
    selected or rescaled. Each draw changes just one constituency vote cell.
    """
    from randomness import random_uniform

    votes = np.asarray(votes, dtype=float)
    parties = np.flatnonzero(np.any(votes > 0, axis=0))
    if not len(parties):
        raise ValueError("Single-list sensitivity requires a positive-vote list.")
    selected = []
    for _ in range(count):
        party = int(parties[int(random_uniform(rng, 0, len(parties)))])
        lists = np.flatnonzero(votes[:, party] > 0)
        constituency = int(lists[int(random_uniform(rng, 0, len(lists)))])
        selected.append((constituency, party))
    draws = generate_votes([votes[c, p] for c, p in selected], cov, distribution, rng)
    for (constituency, party), draw in zip(selected, draws):
        perturbed = votes.copy()
        perturbed[constituency, party] = draw
        yield constituency, party, perturbed


def single_list_category(base, perturbed, constituency, party):
    """Return one of five mutually exclusive outcome indices."""
    if not np.array_equal(base.results["all_grand_total"],
                          perturbed.results["all_grand_total"]):
        return 4
    changed = np.asarray(base.results["all_const_seats"]) != np.asarray(
        perturbed.results["all_const_seats"])
    if changed[constituency, party]:
        return 3
    if base.party_vote_info["specified"]:
        changed = np.vstack((changed, np.asarray(base.results["all_nat_seats"])
                             != np.asarray(perturbed.results["all_nat_seats"])))
    if changed[:, party].any():
        return 2
    return 1 if changed.any() else 0
