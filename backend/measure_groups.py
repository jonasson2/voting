# measureGroups[group]["title"] is the Group heading (in Excel-file column 1)
# MeasureGroups[group]["rows"][measure][0] is measure title, column 1
# MeasureGroups[group]["rows"][measure][1] is measure title, column 2

# Corresponding data is stored in
#   simulation.data[r][m][stat]
# where:
#   r ranges over 0...num_systems-1 (number of electoral systems being simulated)
#   m ranges over the measures, and,
#   stat ranges over "avg", "std", "min", "max", "skw" and "kur"
#
# The system names are in
#   simulation.systems[r].name (r=0,1,...)
#
# The measure-names for comparison with other systems are:
#   cmp_<systemname>_const
#   cmp_<systemname>_tot
#   cmp_<systemname>_nat
# and
#   cmp_<systemname>_grand


from util import disp
from reference_measures import quality_groups, selected_scalings

class MeasureGroups(dict):
    def __init__(self, systems, party_votes_specified, qm_topleft2=None, nr=0,
                 include_entropy_score=False, scalings=("const",)):
        self.update(quality_groups(selected_scalings(scalings),
                                   include_entropy_score, len(systems) > 1))
        if party_votes_specified:
            for extension, title in (("const", "Party totals within constituencies"),
                                     ("nat", "National lists")):
                self[f"party_{extension}"] = {
                    "title": title, "onlyExcel": True,
                    "rows": {
                        f"sum_abs_party_{extension}": ("Half the absolute seat deviation", ""),
                        f"sum_sq_party_{extension}": ("Squared seat deviation", ""),
                    },
                }

        self["cmpListTitle"] = {
            "title": "Absolute seat differences summed over constituency lists",
            "onlyExcel": False,
            "rows": {}
        }
        self["seatSpec"] = {
            "title": "– compared with other seat specifications",
            "rows": {
                "dev_all_adj_const":   ("constituency lists", "all seats as adjustment seats"),
                "dev_all_fixed_const": ("",                 "all seats as fixed seats"),
                "dev_all_adj_tot":     ("party constituency totals","all seats as adjustment seats"),
                "dev_all_fixed_tot":   ("",                 "all seats as fixed seats"),
                "dev_all_adj_nat":     ("national lists",   "all seats as adjustment seats"),
                "dev_all_fixed_nat":   ("",                 "all seats as fixed seats"),
                "dev_all_adj_grand":   ("party grand totals", "all seats as adjustment seats"),
                "dev_all_fixed_grand": ("",                 "all seats as fixed seats"),
                "one_const_tot":       ("",                 "All constituencies combined")
            } if party_votes_specified else {
                "dev_all_adj_const":   ("constituency lists", "all seats as adjustment seats"),
                "dev_all_fixed_const": ("",                 "all seats as fixed seats"),
                "dev_all_adj_tot":     ("party totals","all seats as adjustment seats"),
                "dev_all_fixed_tot":   ("",                 "all seats as fixed seats"),
                "one_const_tot":       ("",                 "All constituencies combined")
            },
            "onlyExcel": True
        }
        self["expected"] = {
            "title": "– compared w. tested systems and source votes",
            "rows": {
                "dev_ref_const": ("constituency lists", ""),
                "dev_ref_tot":   ("party constituency totals", ""),
                "dev_ref_nat":   ("national lists", ""),
                "dev_ref_grand": ("party grand totals", ""),
            } if party_votes_specified else {
                "dev_ref_const": ("constituency lists", ""),
                "dev_ref_tot":   ("party totals", ""),
            },
            "onlyExcel": True
        }
        self["cmpList"] = {
            "title": "",
            "rows": {}
        }
        self["cmpPartyTitle"] = {
            "title": "Total absolute difference in party seats",
            "rows": {}
        }
        self["cmpParty"] = {
            "title": "",
            "rows": {}
        }
        if party_votes_specified:
            self["cmpNationalDetails"] = {
                "title": "Additional national-vote comparison details",
                "rows": {},
                "onlyExcel": True,
            }
        self._add_systems(systems, party_votes_specified, nr)

    def _add_systems(self, systems, party_votes_specified, nr=0):
        list_group = self["cmpList"]["rows"]
        party_group = self["cmpParty"]["rows"]
        for sys in systems:
            measure = "cmp_" + sys["name"] + "_const"
            list_group[measure] = (sys["name"], "")
        for sys in systems:
            suffix = "grand" if party_votes_specified else "tot"
            measure = "cmp_" + sys["name"] + "_" + suffix
            party_group[measure] = (sys["name"], "")
        if party_votes_specified:
            details = self["cmpNationalDetails"]["rows"]
            for sys in systems:
                name = sys["name"]
                details["cmp_" + name + "_tot"] = (
                    "Party constituency totals", name)
                details["cmp_" + name + "_nat"] = (
                    "National lists", name)

    def get_measures(self, group): # get measures from one group
        return self[group]["rows"].keys()
                
    def get_all_measures(self, party_votes_specified):  # get measures from all groups
        measures = []
        for value in self.values():
            add = [x for x in value["rows"].keys()
                   # næsta if þarf hugsanlega ekki
                if party_votes_specified or not x.endswith(('_nat', '_grand'))]
            measures.extend(add)
        return measures

headingType = {
    "shareTitle": "systems",
    "toLists": "empty",
    "toPartiesInConst": "empty",
    "other":      "empty",
    "cmpListTitle": "stats",
    "cmpList":      "systems",
    "cmpPartyTitle": "empty",
    "cmpParty":      "empty",
    "seatSpec":   "systems",
    "expected":   "empty",
    "cmpNationalDetails": "empty"
}

def fractional_digits(group, stat):
    if group in {"seatSpec", "expected", "cmpList", "cmpParty",
                 "cmpNationalDetails"} and stat in {"min", "max"}:
        return 0
    else:
        return 3
