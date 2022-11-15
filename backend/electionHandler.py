from electionSystem import ElectionSystem
from electionSystem import set_one_const, set_const_adj, set_const_fixed
from electionSystem import set_nat_seats, set_nat_seats_adj, set_nat_seats_fixed
from electionSystem import set_custom, set_copy
from voting import Election
from input_util import check_systems
from excel_util import elections_to_xlsx
from util import disp, remove_prefix
from copy import deepcopy

class ElectionHandler:
    """A handler for comparing electoral system results of a single election
    &
    A class for managing comparison of results from different electoral systems,
    on a common vote table.
    """
    def __init__(self, vote_table, systems, use_thresholds):
        systems = check_systems(systems)
        self.votes = vote_table["votes"]
        self.party_vote_info = vote_table["party_vote_info"]
        self.elections = []
        self.setup_elections(vote_table, systems)
        self.run_elections(use_thresholds)

    def run_elections(self, use_thresholds, votes=None, party_votes=None):
        for election in self.elections:
            if votes:
                election.set_votes(votes, party_votes)
            election.run(use_thresholds)
            
    def setup_elections(self, vote_table, systems):
        [constituencies_list,nat_seats] = update_constituencies(vote_table, systems)
        for (system, constituencies, nat) in zip(systems, constituencies_list, nat_seats):
            system["parties"] = vote_table["parties"]
            system["constituencies"] = constituencies
            system["nat_seats"] = nat
            electionSystem = ElectionSystem()
            electionSystem.update(system)
            election = Election(electionSystem,
                                self.votes,
                                party_vote_info=deepcopy(self.party_vote_info),
                                vote_table_name=vote_table["name"])
            self.elections.append(election)

    def to_xlsx(self, filename):
        elections_to_xlsx(self.elections, filename)

def update_constituencies(vote_table, systems):
    constituencies = []
    nat_seats= []
    for system in systems:
        opt = system["seat_spec_options"]["const"]
        opt = remove_prefix(opt, "make_")
        nat = set_nat_seats(vote_table["party_vote_info"])
        voteconst = vote_table["constituencies"]
        if opt in {"const_fixed", "all_fixed"}:
            const = set_const_fixed(voteconst)
            if opt=="all_fixed":
                nat = set_nat_seats_fixed(vote_table["party_vote_info"])
        elif opt in {"const_adj", "all_adj"}:
            const = set_const_adj(voteconst) 
            if opt=="all_adj":
                nat = set_nat_seats_adj(vote_table["party_vote_info"])
        elif opt=="one_const": const = set_one_const(voteconst)
        elif opt=="refer":     const = set_copy(voteconst)
        elif opt=="custom":
            if "constituencies" in system:
                sysconst = system["constituencies"]
                const = set_custom(voteconst, sysconst)
            else:
                const = set_copy(voteconst)
        constituencies.append(const)
        nat_seats.append(nat)
    return (constituencies, nat_seats)
