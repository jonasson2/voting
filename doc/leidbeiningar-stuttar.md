---
title-meta: Kosningahermirinn - Stuttar notkunarleiðbeiningar
lang: is-IS
fontsize: 11pt
papersize: a4
geometry: margin=22mm
mainfont: Georgia
sansfont: Arial
colorlinks: true
---

# Kosningahermirinn

## Til hvers er hermirinn?

Kosningahermirinn er tæki til að gera tilraunir með kosningakerfi. Með honum má
bera saman gildandi kerfi og nýjar hugmyndir, kanna áhrif einstakra reglna og meta
niðurstöðurnar með mismunandi gæðamælikvörðum. Hann getur þannig nýst við þróun
kosningakerfa: prófa má breytingar og kanna bæði kosti þeirra og galla áður en
lengra er haldið.

Hermirinn tekur einkum mið af kosningakerfum Norðurlanda. Í boði eru lögbundnar
reglur um sætaúthlutun fyrir Danmörku, Finnland, Ísland, Noreg og Svíþjóð, og
ennfremur gögn um kjördæmaskipan og kosningaúrslit nokkurra nýlegra kosninga í
þessum löndum. Einnig má breyta reglunum, sameina aðferðir á nýjan hátt og nota
eigin atkvæðagögn og sætaskipan.

Dæmigerð notkun hermisins felst í að velja kosningaúrslit eða hlaða inn
atkvæðatölum ásamt upplýsingum um kjördæma- og sætaskipan. Síðan eru valin eða
skilgreind nokkur kosningakerfi sem bera skal saman. Reikna má sætaúthlutun
samkvæmt þessum kerfum og bera niðurstöðurnar saman. 

Mikilvægara er samt að herma fjölmörg kosningaúrslit með því að hliðra
atkvæðatölunum handahófskennt og úthluta sætum á grundvelli hverra úrslita.
Grunnatkvæðin mynda væntigildi hermdu talnanna og notandi velur fjölda hermana,
líkindadreifingu og staðalfrávik. Öll kerfin fá sömu hermdu atkvæðin. Í lok
hermunarkeyrslu eru ýmsir gæðamælikvarðar reiknaðir fyrir öll samanburðarkerfin
og birtir á skjánum. Einnig er hægt að panta ítarlegri niðurstöður í Excel skrá
sem hlaða má niður til frekari skoðunar og úrvinnslu. Útreiknuðum mælikvörðum
fylgja meðaltöl og staðalfrávik yfir allar hermanirnar og með þeim má m.a.
ákvarða hvort munur á milli kerfa sé tölfræðilega marktækur.

## Dæmi 1: tvö kjördæmi og tveir flokkar

Á *Source votes and seats* velurðu *Use preset* og síðan *2 by 2 example*.
Þar eru þessi grunnatkvæði og sæti:

| Kjördæmi | Föst sæti | Jöfnunarsæti | A | B |
|:---------|----------:|------------:|----:|----:|
| I        | 10        | 2           | 1800 | 2000 |
| II       | 10        | 3           | 2500 | 1700 |

Alls eru því tvö kjördæmi, tveir flokkar, 25 sæti, og 8000 atkvæði. Halda má
þessum gögnum óbreyttum í allri fyrstu tilrauninni.

Í *Electoral systems* gefurðu kerfinu nafnið *D'Hondt*. Bættu síðan við öðru
kerfi með *+*, gefðu því nafnið *Sainte-Laguë* og veldu *Sainte-Laguë* í
öllum þremur *Rule* reitunum. Aðrar stillingar eru þær sömu í báðum kerfum:
engir þröskuldar, *None* við undirbúning og *Maximum constituency seat
share* sem aðferð við úthlutun jöfnunarsæta.

Opnaðu svo *Single election* og skoðaðu bæði kerfin. Bæði gefa A 13 sæti og B
12, en skipta þeim ólíkt milli kjördæma. Með D'Hondt fær A 5 sæti í kjördæmi I
og 8 í kjördæmi II; B fær 7 og 5. Með Sainte-Laguë fær A hins vegar 6 og 7
sæti og B fær 6 í hvoru kjördæmi.

Næst hermum við 5000 kosningar út frá sömu grunnatkvæðum og berum kerfin tvö
saman. Setjum upphafsgildi slembitölugjafans (*random seed*) í 123 svo hægt sé
að endurtaka tilraunina og notum að öðru leyti sjálfgefnar hermunarstillingar.
Þá eru atkvæðin lognormaldreifð, með hlutfallslegu staðalfráviki 25% og fylgni
0,5 milli lista sama flokks. Í hverri hermun fá kerfin sömu atkvæðin og úthluta
sætum samkvæmt sínum reglum.

Skoðum summur algildisfrávika og kvaðrata frávika sætafjölda frá
viðmiðunarsætishlutum (*absolute values* og *squared values*). Yfir listana eru
meðaltölin 1,102 og 0,434 fyrir D'Hondt en 1,085 og 0,417 fyrir Sainte-Laguë.
Paraði munurinn, D'Hondt mínus Sainte-Laguë, er 0,017 ± 0,005 fyrir báða
mælikvarðana. Fyrir heildarsæti flokkanna eru meðaltölin 0,510 og 0,178 fyrir
D'Hondt en 0,496 og 0,164 fyrir Sainte-Laguë; paraði munurinn er 0,014 ± 0,002 í
báðum tilvikum. Öll fjögur 95% öryggisbil munarins eru því ofan við núll svo
Sainte-Laguë gefur marktækt minni frávik samkvæmt þessum fjórum mælikvörðum í
þessu dæmi.

Þetta merkir ekki að Sainte-Laguë sé betri samkvæmt öllum hugsanlegum viðmiðum.
Til dæmis er umframúthlutun á hvert viðmiðunarsæti 0,088 með D'Hondt en 0,094
með Sainte-Laguë og paraði munurinn -0,005 ± 0,001; þar stendur D'Hondt-aðferðin
sig betur, og hún stendur sig líka betur í mestu hlutfallslegu umframúthlutun
(*Greatest relative over-representation*).

## Dæmi 2: íslensku kosningarnar 2024

Veljum nú *Use preset* og íslensku alþingiskosningarnar 2024. Hér eru sex
kjördæmi, 54 föst sæti og níu jöfnunarsæti. Fjöldi beggja tegunda sæta er
ákveðinn í hverju kjördæmi. Dálkarnir sýna listabókstafi flokkanna og í
töflunni *Party names* fyrir neðan atkvæðin má sjá hvaða flokkur stendur að
hverjum lista. Í þessari tilraun ætlum við að bera saman fimm aðferðir við að
staðsetja jöfnunarsætin, en halda öðrum úthlutunarreglum óbreyttum.

Setjum *Small party cutoff* í 2% og ýtum á *Prune small parties*. Þá hverfa L og
Y úr töflunni og níu flokkar standa eftir. Atkvæði þeirra sem voru fjarlægðir,
alls 2257, varðveitast í dálkinum *Pruned* og teljast áfram með þegar
atkvæðahlutföll fyrir þröskulda eru reiknuð.

Veljum kosningakerfi *Iceland (2003–)* undir *Election-law preset*. Kerfið fær
sjálfkrafa nafnið *Iceland*, og D'Hondt-regla helst á öllum þremur
úthlutunarstigunum og stillt er á 5% landsþröskuld fyrir jöfnunarsæti. Bætum
síðan við fjórum kerfum með *+*. Nýtt kerfi tekur stillingar þess fyrra, svo 5%
þröskuldurinn og D'Hondt-reglurnar fylgja sjálfkrafa með. Breytum aðeins nafni
hvers kerfis og *Allocation method* undir *Allocation of adjustment seats to
lists* sem hér segir:

- Nafn *Optimal* og aðferð *Optimal LP*,
- *Max seat share* og *Maximum constituency seat share*,
- *Switching* og *Switching of seats*,
- *Rel-sup-simple* og *Relative superiority, simplified*.

Skoðum fyrst *Single election*. Öll fimm kerfin gefa B 5 sæti, C 11, D 14, F 10,
M 8 og S 15, en J, P og V ekkert sæti. Þau úthluta líka föstu sætunum eins;
munurinn er í hvaða kjördæmum jöfnunarsæti flokkanna lenda. Tölur í svigum sýna
jöfnunarsætin og skrefatöflurnar fyrir neðan sýna hvernig þeim er úthlutað. Í
öllum tilvikum þarf að færa fjögur sæti milli lista til að breyta úthlutun
*Iceland* í úthlutun hinna kerfanna, sem eru þó ekki öll eins: *Optimal* og
*Rel-sup-simple* gefa sömu úthlutun, en *Switching* og *Max seat share* gefa
hvort sína úthlutun.

Hermum næst 2000 kosningar með upphafsgildi slembitölugjafans (*random seed*)
1234, en höldum öðrum stillingum óbreyttum eins og sjálfgefið er og ýtum á
*Start simulation*. Byrjum á fyrstu línu niðurstaðna, *Absolute values (Hare
quota)*, í hlutanum *Differences between allocated and fractional reference
seats, summed over constituency lists*. Þar eru algildi frávika úthlutaðra sæta
frá brotnum viðmiðunarsætishlutum lögð saman og summunni deilt með tveimur. Hver
eining í summunni telur því tilfærslu eins sætis frá einum lista til annars.
Meðaltölin eru 9,36 fyrir *Iceland*, 8,88 fyrir *Optimal*, 8,95 fyrir *Max seat
share*, 8,89 fyrir *Switching* og 8,90 fyrir *Rel-sup-simple*. Dálkurinn
*Difference* sýnir paraðan mun fyrstu tveggja kerfanna: 0,49 ± 0,03.
Öryggisbilið er vel ofan við núll, svo frávikin eru að meðaltali marktækt meiri
með íslensku aðferðinni en þeirri bestu samkvæmt þessum mælikvarða.

Hinar línurnar í þessum hluta leggja mismunandi áherslu á stærð frávika,
umframúthlutun og vanúthlutun, ýmist í sætum eða miðað við stærð listanna.
Heildarmyndin er svipuð: *Optimal* hefur lægstu meðaltölin í sex af sjö línum
og *Iceland* þau hæstu í sex. *Switching* og *Rel-sup-simple* standa sig svipað
og báðar yfirleitt nokkru betur en *Max seat share*, en röðin er ekki alstaðar
eins.

Í næsta hluta, *Party seat totals: allocated minus fractional reference*,
eru allar niðurstöður eins fyrir kerfin fimm, bæði meðaltöl og öryggisbil.
Ástæðan er að föstu sætin, landsúthlutun flokkanna og þröskuldarnir eru eins
í öllum kerfunum. Þau gefa hverjum flokki því sama heildarsætafjölda í hverri
einustu hermun.

Í þriðja hlutanum, *Specific quality indices for allocations in the
constituencies*, skoðum við fyrst *Entropy score*, óreiðustigið. Það sýnir
hlutfall margfeldis kvóta úthlutaðra sæta af stærsta mögulega margfeldinu
samkvæmt valinni reglu og sömu skorðum. *Optimal* fær því 100%. Samkvæmt þessu
viðmiði er *Rel-sup-simple* næst bestu úthlutuninni, síðan *Switching* og *Max
seat share*, en *Iceland* lengst frá henni. Hér greinast *Switching* og
*Rel-sup-simple* betur að en í fyrstu töflunni. Athuga skal að óreiðustigið
metur aðeins úthlutun jöfnunarsætanna en leggur engan mælikvarða á gæði
kjördæmaúthlutunarinnar eða ákvörðun heildarsæta hvers flokks; 100% merkir því
ekki að kosningakerfið í heild sé besta mögulega kerfið.

Næstu tvær línur í þriðja hlutanum mæla misvægi milli kjördæma: Sú fyrri segir
að færa þurfi rétt um 5 sæti milli kjördæma til að ná jafnvægi þannig að
sætafjöldinn endurspegli atkvæðafjölda, og sú seinni segir að 1,88 sinnum fleiri
atkvæði séu að baki hverju sæti þar sem þau eru flest en þar sem þau eru fæst.
Með því skoða atkvæðatöfluna sést að munurinn er mestur milli NV og SV. Allir
dálkarnir gefa sömu tölur því fyrstu tvö úthlutunarskref allra kerfanna eru hin
sömu.

Skoðum loks *Absolute seat differences summed over constituency lists*.
Þar eru kerfin borin saman tvö og tvö og hver tala segir hversu mörg sæti
þurfi að færa milli lista að meðaltali til að breyta annarri úthlutuninni í
hina. Í röðinni fyrir *Optimal* eru gildin 3,35 fyrir *Iceland*, 2,47 fyrir
*Max seat share*, 1,76 fyrir *Switching* og 1,15 fyrir *Rel-sup-simple*.
Þetta segir sömu sögu og óreiðustigið: *Rel-sup-simple* er næst bestu
úthlutuninni, síðan kemur *Switching*, þá *Max seat share* og loks *Iceland*.

## Gamalt:

Stillingin *Simulate with thresholds?* skiptir máli við samanburð kerfa með
þröskulda. Valið *No* gerir kleift að skoða kerfin án stökka sem verða
þegar flokkur fer yfir eða undir þröskuld. Það slekkur á þröskuldum og öðrum
hæfisskilyrðum flokka, nema *Stand in all constituencies*. Niðurstöðurnar
lýsa þá ekki lengur kerfunum með öllum upphaflegum skilyrðum þeirra.

Helstu niðurstöður sjást á vefsíðunni. *Download Excel file* á
niðurstöðuflipunum gefur ítarlegri töflur til skoðunar og frekari úrvinnslu. Til
dæmis má finna viðmiðunarsætishlutina í Excel-skrá hermunar. Í *Settings* má
velja talnasnið og fjölda aukastafa; það breytir framsetningu en ekki
útreikningunum.

## Eigin gögn og aðrar tilraunir

Atkvæðatöflunni má breyta beint eða lesa hana úr Excel- eða CSV-skrá með
*Upload from file*. Auðveld leið til að útbúa eigin skrá er að hlaða niður
atkvæðatöflu úr herminum, breyta henni og hlaða henni inn aftur. Þá þarf ekki
að smíða skráarsniðið frá grunni.

## Vista, hlaða inn og halda áfram

Til að varðveita tilraun er yfirleitt best að nota *Download all*. Það vistar
atkvæðatöfluna, öll skilgreind kosningakerfi og hermunarstillingarnar í einni
JSON-skrá. Með *Upload all* má síðar hlaða þessum forsendum inn aftur eða
flytja þær á aðra tölvu. Hermunarniðurstöðurnar sjálfar fylgja ekki með.

Einnig má vista einstaka hluta:

- *Atkvæði og sætaskipan:* *Download* á *Source votes and seats* vistar
  Excel-skrá. Hún er lesin með *Upload from file*.
- *Kerfi og hermunarstillingar, án atkvæða:* *Download* á *Electoral
  systems* vistar JSON-skrá. *Upload* kemur í stað núverandi kerfa;
  *Append from file* bætir kerfum við þau sem fyrir eru.
- *Reiknaðar niðurstöður:* *Download Excel file* á *Single election* eða
  *Simulated elections*. Þessar skrár eru ætlaðar til skoðunar og úrvinnslu,
  ekki til að endurhlaða tilrauninni.

Ef þú vilt varðveita bæði forsendur og niðurstöður skaltu því sækja bæði
JSON-skrána með *Download all* og viðeigandi Excel-skrá með niðurstöðum.
Skráðu einnig hvaða útgáfa hermisins var notuð. Tilgreint upphafsgildi
slembitölugjafans (*random seed*) auðveldar að endurtaka keyrsluna með sömu
gögnum og stillingum.

## Þegar lengra er haldið

Veldu ákveðna spurningu fyrir hverja tilraun: Viltu bæta hlutfallslega
skiptingu milli flokka, dreifingu sæta innan flokka eða stöðugleika gagnvart
litlum atkvæðabreytingum? Breyttu einu atriði í senn þegar þú vilt rekja áhrif
þess og haltu öðrum forsendum föstum.

Prófaðu síðan fleiri grunnúrslit og mismikla dreifingu atkvæða. Eitt dæmi eða
einn mælikvarði nægir sjaldnast til að meta kerfi. Við túlkun óreiðu og annarra
gæðamælikvarða skiptir máli hvaða viðmið og skorður liggja að baki: besta
niðurstaðan samkvæmt einu viðmiði þarf ekki að vera sú besta samkvæmt öðru.
