import csv
flo = {}
kjd = {}
ár = {}
tafla = {}
ár['25. apríl 1987'] = "1987"
ár['20.apr.91'] = "1991"
ár['8. apríl 1995'] = "1995"
ár['8. maí 1999'] = "1999"

with open("kjordaemi.csv") as kj:
    for (skst,kjörd) in csv.reader(kj):
        kjd[kjörd] = skst
nkjördæmi = len(kjd)

tafla = {}
flokkar = {}

for y in ár.values():
    tafla[y] = [[] for i in range(nkjördæmi)]
    flokkar[y] = []

with open("flokkar.csv") as fl:
    for (skst,flokkur) in csv.reader(fl, delimiter="\t"):
        flo[flokkur] = skst

with open("hagstofa.csv") as ha:
    reader = csv.reader(ha, quoting=csv.QUOTE_NONNUMERIC, delimiter=";")
    kjördæmi = next(reader)[2:]
    for L in reader:
        dags = L[0]
        y = ár[dags]
        fl = flo[L[1]]
        flokkar[y].append(fl)
        atkv = L[2:]
        if not sum(atkv): continue
        for k in range(nkjördæmi):
            tafla[y][k].append(atkv[k])

print(kjd.values())
            
for y in ár.values():
    l = [len(f) for f in flokkar[y]]
    print(l)
    with open("island-" + y + ".csv") as f:
    print()
    print(f'{y:15}
    for k in range(nkjördæmi):
        kd = list(kjd.values())[k]
        print(f'{kd:15}  ',end='')
        for a in tafla[y][k]: print(f'{a:6.0f} ', end='')
        print()
