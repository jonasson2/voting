"""Settings summaries shared by CSV and Excel simulation reports."""

from reference_measures import selected_scalings, SCALINGS


def simulation_settings(results):
    settings = results["sim_settings"]
    rows = [
        {"label": "Number of replicates", "data": results["iteration"]},
        {"label": "Random seed", "data": settings.get("random_seed", "")},
        {"label": "Generating method", "data": settings["gen_method"]},
        {"label": "Relative standard deviation for list votes",
         "data": settings["const_rsd"]},
        {"label": "Correlation between list votes within each party",
         "data": settings["const_corr"]},
    ]
    if results["vote_table"]["party_vote_info"]["specified"]:
        rows.extend((
            {"label": "Relative standard deviation for national party votes",
             "data": settings["party_vote_rsd"]},
            {"label": "Correlation between list votes and national party votes",
             "data": settings["party_vote_corr"]},
        ))
    rows.extend((
        {"label": "Thresholds used",
         "data": "yes" if settings["use_thresholds"] else "no"},
        {"label": "Entropy score calculated",
         "data": "yes" if settings["entropy_score"] else "no"},
        {"label": "Reference scaling benchmarks",
         "data": ", ".join(SCALINGS[key] for key in selected_scalings(settings.get("scaling", list(SCALINGS)))) or "Dedicated local indices only"},
    ))
    if settings.get("sensitivity"):
        rows.append({"label": "Sensitivity measures calculated", "data": "yes"})
    if settings.get("single_list_sensitivity"):
        rows.append({"label": "Single-list sensitivity calculated", "data": "yes"})
        rows.append({"label": "Single-list perturbations per major simulation",
                     "data": settings["single_list_simulation_count"]})
    if settings.get("sensitivity"):
        rows.append({"label": "Number of perturbations per major simulation",
                     "data": settings["sensitivity_simulation_count"]})
    if settings.get("sensitivity") or settings.get("single_list_sensitivity"):
        rows.extend((
            {"label": "Sensitivity generating method",
             "data": settings["sensitivity_gen_method"]},
            {"label": "Sensitivity CoVs (%)",
             "data": " ".join(
                 f"{value:g}" for value in settings["sensitivity_covs"])},
        ))
    return rows


def source_settings(results):
    vote_table = results["vote_table"]
    return [
        ("Votes-and-seats table", vote_table["name"]),
        ("Number of constituencies", len(vote_table["constituencies"])),
        ("Number of parties", len(vote_table["parties"])),
        ("Total number of const. seats", sum(
            constituency["num_fixed_seats"]
            for constituency in vote_table["constituencies"])),
        ("Total number of adj. seats", sum(
            constituency["num_adj_seats"]
            for constituency in vote_table["constituencies"])),
        ("Total number of const. votes",
         sum(map(sum, vote_table["votes"])) + sum(vote_table.get("pruned", []))),
        ("Total number of national party votes",
         vote_table["party_vote_info"]["total"]),
    ]
