"""Vote perturbation and seat-displacement helpers for sensitivity analysis."""

import numpy as np

from generate_votes import generate_votes


def sensitivity_covs(percentages):
    """Validate percentage values and return CoVs as fractions."""
    if not isinstance(percentages, list) or not percentages:
        raise ValueError("Specify at least one sensitivity CoV.")
    try:
        values = [float(value) for value in percentages]
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Sensitivity CoVs must be positive numbers.") from error
    if any(not np.isfinite(value) or value <= 0 for value in values):
        raise ValueError("Sensitivity CoVs must be positive numbers.")
    if any(left >= right for left, right in zip(values, values[1:])):
        raise ValueError(
            "Sensitivity CoVs must be distinct and in increasing order.")
    return [value / 100 for value in values]


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
