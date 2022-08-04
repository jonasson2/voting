from electionSystem import ElectionSystem
from electionSystem import set_one_const, set_all_adj, set_all_fixed
from electionSystem import set_custom, set_copy
from voting import Election
from table_util import add_totals
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
        constituencies_list = update_constituencies(vote_table, systems)
        for (system, constituencies) in zip(systems, constituencies_list):
            system["parties"] = vote_table["parties"]
            system["constituencies"] = constituencies
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
    for system in systems:
        opt = system["seat_spec_options"]["const"]
        opt = remove_prefix(opt, "make_")
        voteconst = vote_table["constituencies"]
        if opt=="all_fixed":   const = set_all_fixed(voteconst)
        elif opt=="all_adj":   const = set_all_adj(voteconst)
        elif opt=="one_const": const = set_one_const(voteconst)
        elif opt=="refer":     const = set_copy(voteconst)
        elif opt=="custom":
            if "constituencies" in system:
                sysconst = system["constituencies"]
                const = set_custom(voteconst, sysconst)
            else:
                const = set_copy(voteconst)
        constituencies.append(const)
    return constituencies
