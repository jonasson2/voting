import pandas as pd, numpy as np
from numpy import NaN

# The files read here are from:
# (1) https://www.bundeswahlleiter.de/bundestagswahlen/2013/ergebnisse.html
#     and select Tabellen: Endgültige Ergebnisse nach Wahlkreisen aller Bundestagswahlen
# (2) https://www.bundeswahlleiter.de/bundestagswahlen/2017/ergebnisse.html
#     and select "Tabelle...tabellarischer Aufbau"
# (3) https://www.bundeswahlleiter.de/bundestagswahlen/2021/ergebnisse/opendata/csv/

parties = ['SPD', 'FDP', 'Grüne', 'PDS', 'Linke', 'AfD', 'CDU', 'other']
years = [1990, 1994, 1998, 2002, 2005, 2009, 2013, 2017, 2021]

def fill_in_party(columns):
    level0 = [c[0] for c in columns]
    level1 = [c[1] for c in columns]
    level2 = [c[2] for c in columns]
    fill = '-'
    for i in range(len(level0)):
        if level0[i].startswith('Unnamed'):
            level0[i] = fill
        else:
            fill = level0[i]
    newcols = list(zip(level0, level1, level2))
    return pd.MultiIndex.from_tuples(newcols)

def pandas_all():
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

pandas_all()

def combine_grüne(df):
    if 'B90/Gr' in df.columns:
        df.Grüne += df['B90/Gr']

def combine_CDU_CSU(df):
    df.CDU += df.CSU

def select_parties(dfin):
    party_replace = {
        "DIE LINKE": "Linke",
        "Die Linke.": "Linke",
        "GRÜNE": "Grüne",
        "F.D.P.": "FDP",
        "Christlich Demokratische Union Deutschlands": "CDU",
        "Sozialdemokratische Partei Deutschlands": "SPD",
        "Alternative für Deutschland": "AfD",
        'Freie Demokratische Partei': "FDP",
        "BÜNDNIS 90/DIE GRÜNEN": "Grüne",
        "Christlich-Soziale Union in Bayern e.V.": "CSU",
    }
    df = dfin.copy()
    df.rename(columns=party_replace, inplace=True)
    df.rename(columns={'Gültige Stimmen': 'Gültige'}, inplace=True)
    combine_grüne(df)
    combine_CDU_CSU(df)
    select = [s for s in parties if s in df.columns and s != "other"]
    gültige = df.Gültige
    df = df[select]
    df.loc[:,'other'] = gültige - df.sum(axis=1)
    return df

def read_one_year(yr):
    file = f'./kerg/btw{yr}_kerg.csv'
    if yr <= 2002:
        df = pd.read_csv(file, sep=';', decimal=',', header = [5,6])
        df.dropna(axis=0, how='all', inplace=True)
        nr = df.xs('Wahlkreis',axis=1,drop_level=True).astype(int)
        name = df.xs('Name', axis=1, level=1)
        name.columns = ['Name']
        nr_name = pd.concat((nr,name), axis=1)
        nr_name.columns = ['Nr', 'Name']
        nr_name.Name = nr_name.Name.str.replace('\226', '-')
        erst = df.xs('Erststimmen', axis=1, level=1, drop_level=True)
        zweit = df.xs('Zweitstimmen', axis=1, level=1, drop_level=True)
    else:
        header = [5,6,7] if yr < 2021 else [2,3,4]
        df = pd.read_csv(file, sep=';', decimal=',', header=header,
            skip_blank_lines = True)
        df.dropna(axis=0, how='all', inplace=True)
        df.fillna(0, inplace=True)
        df.Nr = df.Nr.astype(int)
        df.columns = pd.MultiIndex.from_tuples(fill_in_party(df.columns))
        nr_name = df[['Nr', 'Gebiet']].copy()
        nr_name.columns = nr_name.columns.droplevel((1, 2))
        nr_name.columns = ['Nr', 'Name']
        nr_name.Name = nr_name.Name.str.replace(chr(8211), '-')
        if yr > 2013:
            gehört = df.xs('gehört zu', axis=1, drop_level=False)
            gehört.columns = gehört.columns.droplevel((1,2))
            land_row = gehört['gehört zu'] == 99
            nr_name.loc[land_row, 'Nr'] = nr_name.loc[land_row, 'Nr'] + 900
        erst = df.xs(('Erststimmen','Endgültig'), axis=1, level=(1,2), drop_level=True)
        zweit = df.xs(('Zweitstimmen','Endgültig'), axis=1, level=(1,2), drop_level=True)
    erst = select_parties(erst)
    zweit = select_parties(zweit)
    erst = pd.concat((nr_name, erst), axis=1)
    zweit = pd.concat((nr_name, zweit), axis=1)
    return erst, zweit

def extract_länder(zweit):
    select = (900 < zweit.Nr) & (zweit.Nr <= 916)
    zweit = zweit[select].copy()
    zweit['Nr'] = zweit.Nr - 900
    zweit.set_index('Nr',drop=True,inplace=True)
    return zweit.sort_index()

def split_kerg_into_kreise(erst):
    const = [None]*17
    begin = 0
    for i in range(len(erst)):
        Nr = erst.iloc[i,0]
        if 900 < Nr < 917:
            land = Nr - 901
            const[land] = erst.iloc[begin:i,:]
            const[land].reset_index(drop=True, inplace=True)
            begin = i+1
    return const

def read_kerg1():
    const_votes = []
    party_votes = []
    for yr in years:
        print(yr)
        (erst, zweit) = read_one_year(yr)
        erst = split_kerg_into_kreise(erst)
        zweit = extract_länder(zweit)
        const_votes.append(erst)
        party_votes.append(zweit)
    pass
    return const_votes, party_votes

def to_json(pvotes, cvotes, const, parties, länder):
    import json
    colors = {
        "SPD":   'orangered',
        "AfD":   'dodgerblue',
        "FDP":   'goldenrod',
        "PDS":   'MediumVioletRed',
        "Linke": 'violet',
        "Grüne": 'mediumseagreen',
        "CDU":   'black',
        "other": 'darkgray',
        }
    cv = [[[v for (c,v) in cvpl.items()] for cvpl in cvp] for cvp in cvotes]
    with open('partyvotes.json', 'w') as f:
        json.dump({
            'pv':      [v.tolist() for v in pvotes],
            'cv':      cv,
            'const':   const,
            'parties': parties,
            'lander':  länder.tolist(),
            'colors':  [colors[p] for p in parties],
            'years':   years,
        }, f)

np.set_printoptions(suppress=True, floatmode="fixed", precision=2, linewidth=130)
cv, pv = read_kerg1()
länder = pv[0].Name
nparty = len(parties)
nland = len(länder)
nyear = len(years)

# PARTY VOTES (ZWEITSTIMMEN)
pvotes = [None]*nparty
for (party_number, party) in enumerate(parties):
    pvotes[party_number] = np.zeros((16, nyear))
    for (election_number, df) in enumerate(pv):
        pvotes[party_number][:,election_number] = df[party].values if party in df else NaN

# CONSTITUENCY VOTES (ERSTSTIMMEN), GET SETS OF ALL CONSTIUENCIES IN EACH LAND
const = [None]*nland
for l in range(nland):
    C = set()
    for yr in range(nyear):
        Name = cv[yr][l].Name
        C |= set(Name)
    const[l] = list(C)

# CONSTRUCT DICTIONARIES CONST -> [VOTES-1990,...,VOTES2021] FOR EACH PARTY,LAND
cvotes = [[{} for _ in range(nland)] for _ in range(nparty)]
for p in range(nparty):
    for l in range(nland):
        for c in const[l]:
            cvotes[p][l][c] = [NaN]*nyear

# POPULATE THE DICTIONARIES
for l in range(nland):
    nconst = len(const[l])
    for yr in range(nyear):
        df = cv[yr][l]
        constituency = df.Name
        for p, party in enumerate(parties):
            if party in df:
                cvotespl = cvotes[p][l]
                for (i,c) in enumerate(df.Name):
                    cvotespl[c][yr] = float(df[party][i])

# WRITE TO JSON FILE
to_json(pvotes, cvotes, const, parties, länder)

pass