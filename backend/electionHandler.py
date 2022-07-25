from electionSystem import ElectionSystem
from electionSystem import set_one_const, set_all_adj, set_all_const
from electionSystem import set_custom, set_copy
from voting import Election
from table_util import add_totals
from input_util import check_vote_table, check_systems
from excel_util import elections_to_xlsx
from util import disp, remove_prefix
from copy import deepcopy

class ElectionHandler:
    """A handler for comparing electoral system results of a single election
    &
    A class for managing comparison of results from different electoral systems,
    on a common vote table.
    """
    def __init__(self, vote_table, systems, min_votes=0):
        systems = check_systems(systems)
        vote_table = check_vote_table(vote_table)
        self.votes = vote_table["votes"]
        self.party_votes = vote_table["party_votes"]
        self.set_min_votes(min_votes)
        self.elections = []
        self.setup_elections(vote_table, systems)
        self.run_elections()

    def run_elections(self, votes=None, threshold=True):
        for election in self.elections:
            if votes:
                election.set_votes(votes)
            election.run()
            
    def setup_elections(self, vote_table, systems):
        constituencies_list = update_constituencies(vote_table, systems)
        for (system, constituencies) in zip(systems, constituencies_list):
            system["parties"] = vote_table["parties"]
            system["constituencies"] = constituencies
            electionSystem = ElectionSystem()
            electionSystem.update(system)
            name = vote_table["name"] + ":" + system["name"]
            election = Election(electionSystem,
                                self.votes,
                                party_votes=self.party_votes,
                                name=name)
            self.elections.append(election)

    def to_xlsx(self, filename):
        elections_to_xlsx(self.elections, filename)

    def set_min_votes(self, min_votes):
        for row in self.votes:
            for i in range(len(row)):
                row[i] = max(min_votes, row[i])

def update_constituencies(vote_table, systems):
    constituencies = []
    for system in systems:
        opt = system["seat_spec_options"]["const"]
        opt = remove_prefix(opt, "make_")
        voteconst = vote_table["constituencies"]
        if opt=="all_const":   const = set_all_const(voteconst)
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
