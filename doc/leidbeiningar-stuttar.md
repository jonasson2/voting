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

Næst opnum við *Simulated elections* og hermum 5000 kosningar út frá sömu
grunnatkvæðum og berum kerfin tvö saman. Setjum upphafsgildi slembitölugjafans
(*random seed*) í 123 svo hægt sé að endurtaka tilraunina og notum að öðru leyti
sjálfgefnar hermunarstillingar. Þá eru atkvæðin lognormaldreifð, með
hlutfallslegu staðalfráviki 25% og fylgni 0,5 milli lista sama flokks. Í hverri
hermun fá kerfin sömu atkvæðin og úthluta sætum samkvæmt sínum reglum.

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

Prófum loks að breyta atkvæðum A í kjördæmi I úr 1800 í 1200 *Single election*.
Undir D'Hondt birtist viðvörunin **Tied allocation scores** ásamt nánari
útlistun. Fyrsta jafnteflið er þegar í kjördæmi I þegar deilt er í atkvæði A með
3 og B með 5 (bæði gefur 400), og hin jafnteflin þegar summur flokkanna eru
reiknaðar; það kemur ekki á óvart því báðir flokkar eru með nákvæmlega helming
atkvæðanna. Hermirinn gefur A síðasta sætið en í raun gæti það allt eins lent
hjá B þegar varpað væri hlutkesti. Breytum atkvæðum A í kjördæmi I aftur 1800
áður en haldið er áfram.

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

Skoðum loks *Absolute seat differences summed over constituency lists*. Þar eru
kerfin sem merkt er við undir *Electoral systems used for comparison* ("öll" er
sjálfgefið) borin saman tvö og tvö og hver tala segir hversu mörg sæti þurfi að
færa milli lista að meðaltali til að breyta annarri úthlutuninni í hina. Í
röðinni fyrir *Optimal* eru gildin 3,35 fyrir *Iceland*, 2,47 fyrir *Max seat
share*, 1,76 fyrir *Switching* og 1,15 fyrir *Rel-sup-simple*. Þetta segir sömu
sögu og óreiðustigið: *Rel-sup-simple* er næst bestu úthlutuninni, síðan kemur
*Switching*, þá *Max seat share* og loks *Iceland*.

========================== Kominn hingað =====================================
Hér dettur mér í huga að halda áfram á þessa leið:

Taka þriðja dæmið sem er Noregur 2025, og kynna þar til sögu atriði sem ekki hafa
verið nefnd enn:

- Hermun án þröskulda. Ég prófaði t.d. sjálfgefið kerfi og setti báða "National
thresholds" 4%, seed 123 og hermunarstaðalfrávik 0.75. Þá fæst með þröskuldum
efstu tvö staðalfrávikin í hermun 2.39 og 7.49 en án þeirra 2.02 og 4.34. 
- segja frá Download Excel
- Settings
- Download og Upload
- Etv. sýna dæmi um fjölgun jöfnunarsæta og hvernig þá næst betri jöfnuður milli
  kjördæma
- Sýna næmni

Koma svo með kafla sem nefnir ýmsa fídusa sem enn hafa ekki verið nefndir:
- National party votes
- Aðrar hermunarstillingar: Vote scaling, aðrar dreifingar, fylgni, #CPUs og
  möguleiki á að sleppa óreiðureikningum (sparar smá tíma). Etv. nefna Stop
  simulation og tímann sem hermun tekur?
- Flex jöfnunarsæti, nefna að þau komi við sögu í Svíðþjóð og Danmörku (ég hafði
  reyndar hugsað mér að taka dæmið um Svíþjóð, segja að þeirra aðferð sé
  sjálfkrafa sú sama og optimal, en benda á að það sé á kostnað "Geographical
  seat displacement" sem er hærra en ef maður festir jöfnunarsætin með
  "Distribute adjustment seats by Adams í "Alternative specification of fixed
  and adjustment seats" [var aðeins að hugsa um að hafa stutt dæmi um Svíðþjóð
  þar sem þetta er gert?]. 
- Nefna "All fixed" og "All adjustment"?
  
Læt þetta duga. 

Kristján
