import sys
sys.path.append("../backend")
import numpy as np
from util import disp

def readkerg():
    import openpyxl
    kergfile = "þýskaland-2021.xlsx"
    book = openpyxl.load_workbook(kergfile)

    def get1dict(sheet, col=1):
        rows = iter(book[sheet].rows)
        dictionary = {}
        next(rows)
        for row in rows:
            dictionary[row[0].value-1] = row[col].value
        return dictionary
    def getconst(sheet, nland):
        rows = iter(book[sheet].rows)
        dict1 = {}
        dict2 = {}
        next(rows)
        const = [[] for _ in range(nland)]
        for row in rows:
            constnr, constituency, landnr = (r.value for r in row[0:3])
            const[landnr-1].append(constituency)
        return const

    land = get1dict("Land")
    land_seat_dict = get1dict("Land", 2)
    land_seats = [land_seat_dict[i] for i in range(len(land_seat_dict))]
    party = get1dict("Partei")
    party[len(party.keys())] = 'other'
    nland = len(land)
    nparty = len(party)
    const = getconst("Kreis", nland)
    nconst = [len(c) for c in const]

    def get_party_votes():
        rows = iter(book["Zweitstimme"].rows)
        next(rows)
        party_votes = np.zeros((nland, nparty), int)
        party_vote_pct = np.zeros((nland, nparty - 1))
        for row in rows:
            (l, p, v, pct) = (row[0].value, row[1].value, row[2].value, row[3].value/100)
            if p==37:
                p = 8
            party_votes[l-1,p-1] = v
            party_vote_pct[l-1,p-1] = pct
        for l in range(nland):
            pct_sum = party_vote_pct[l,:].sum()
            other_votes = np.round(party_votes[l,:-1].sum()*(1 - pct_sum)/pct_sum)
            party_votes[l,-1] = other_votes.astype(int)
        return party_votes

    def get_const_votes():
        rows = iter(book["Erststimme"].rows)
        next(rows)
        votes = [None]*nland
        vote_pct = [None]*nland
        llast = None
        for r in rows:
            (c,l,p,v,vp) = (r[0].value, r[1].value, r[2].value, r[3].value,r[4].value/100)
            if p==37:
                p = 8
            if l != llast:
                votes[l-1] = np.zeros((nconst[l-1], nparty), int)
                vote_pct[l-1] = np.zeros((nconst[l-1], nparty))
                llast = l
                c0 = c
            votes[l-1][c-c0,p-1] = v
            vote_pct[l-1][c-c0,p-1] = vp
        for l in range(nland):
            for c in range(nconst[l]):
                pct_sum = vote_pct[l][c,:].sum()
                other_votes = np.round(votes[l][c,:-1].sum()*(1 - pct_sum)/pct_sum)
                votes[l][c,-1] = other_votes.astype(int)
        return votes

    party_votes = get_party_votes()
    const_votes = get_const_votes()
    votes = [np.array(cv) for cv in const_votes]
    data = {"landseats": land_seats, "partyvotes": party_votes, "constvotes": votes}
    info = {"land": land, "party": party, "const": const}
    return info, data
