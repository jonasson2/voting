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

## Fyrsta tilraun: tvö kjördæmi og tveir flokkar

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

## Önnur tilraun: sænsku kosningarnar 2026

Veldu *Use preset* og síðan sænsku þingkosningarnar 2026. Hér eru raunveruleg
atkvæðagögn í mun stærri töflu en í fyrri tilrauninni: 29 kjördæmi og fjölmargir
flokkar. Tilraunin sýnir hvernig sænska kerfið er sett upp og hvernig bera má
það saman við aðrar aðferðir við úthlutun jöfnunarsæta.

Atkvæðataflan sýnir 310 föst sæti. Lágmark jöfnunarsæta er núll í hverju
kjördæmi og bandstrik í dálkinum *# Max adj.* merkir að þar sé ekkert fyrirfram
ákveðið hámark. Í reitnum *Adjustment seats to allocate* ofan við töfluna
stendur 39, svo alls eru 349 þingsæti. Jöfnunarsætunum 39 er dreift milli
flokkanna þannig að þingsætahlutfall hvers flokks verði sem næst hlutfalli hans
af atkvæðum á landsvísu. Jöfnunarsætum hvers flokks er síðan dreift milli
kjördæma þannig að dreifing heildarsæta hans endurspegli dreifingu atkvæða hans
sem best.

Eins og sést eru ótal flokkar í framboði, margir smáflokkar og sumir fá aðeins 1
eða 2 atkvæði. Til að fækka þeim má velja *Prune small parties*. Þá standa eftir
átta flokkar sem allir hafa meira en 5% atkvæða. Þessi stytting er aðeins gerð
til að einfalda tilraunina; 1% er ekki sænskur úthlutunarþröskuldur.

Næst skal fara í *Electoral systems* og láta *Election law preset* vera *Sweden
(2018–)*. Bættu svo við tveimur samanburðarkerfum,

Veldu *Sweden (2018–)* undir *Election-law preset*. Fyrirmyndin
stillir meðal annars 4% landsþröskuld, 12% staðbundinn þröskuld og breyttu
Sainte-Laguë-regluna með fyrsta deili 1,2. Hún velur einnig *Swedish switching*
sem undirbúning fyrir úthlutun jöfnunarsæta og *Maximum constituency votes*
sem aðferð við lokaúthlutun þeirra.

Reiknaðu úrslitin og skoðaðu skrefatöflurnar. Fyrst eru föstu sæti hvers
flokks borin saman við þann heildarsætafjölda sem flokknum ber á landsvísu. Ef
flokkur hefur fengið of mörg föst sæti eru umframsæti hans færð til flokka sem
vantar sæti. Þetta er *Swedish switching*. Í kosningunum 2026 þarf þó enga
slíka færslu og það kemur fram í fyrri skrefatöflunni. Í þeirri síðari sést
hvernig jöfnunarsætunum 39 er úthlutað eitt af öðru.

Til að kanna áhrif lokaúthlutunarinnar skaltu bæta við öðru kerfi og velja þar
einnig *Sweden (2018–)*. Nefndu kerfin til dæmis *Swedish method* og *Vote
percentage*. Í seinna kerfinu breytirðu aðeins *Allocation method* úr *Maximum
constituency votes* í *Maximum constituency vote percentage*. Landsúthlutun
flokkanna og hugsanleg sænsk skipti eru þá óbreytt, en önnur regla ræður í hvaða
kjördæmum jöfnunarsætin lenda.

Fyrir þessi atkvæði fá flokkarnir sömu heildarsætatölur í báðum kerfum, en
sætaskiptingin milli kjördæmalista verður talsvert ólík. Færa þarf 27 sæti milli
kjördæmalista til að breyta annarri úthlutuninni í hina. Með hermun má síðan
bera aðferðirnar saman yfir mörg möguleg atkvæðamynstur. Samanburður
heildarsæta flokka á að vera núll, því kerfin ákvarða þau eins, en mælikvarðar
á úthlutun til kjördæmalista geta verið ólíkir.

## Hermun og samanburður

Fyrsta tilraunin notar sjálfgefin gildi á *Simulated elections*, að
undanskildum fjölda hermana, sem er settur í 5.000, og upphafsgildi
slembitölugjafans (*random seed*), sem er sett í 123. Bandstrikið *-* lætur
herminn velja nýjar slembitölur. Bæði kerfin eru sjálfgefið valin undir
*Electoral systems used for comparison*. Ýttu á *Start simulation* til
að hefja hermunina. Stillingar fyrir sérstök landsatkvæði koma ekki við sögu
í þessu dæmi.

Í hverri hermun fá bæði kerfin sömu atkvæðin. Því er eðlilegt að bera kerfi
saman í sömu keyrslu. Byrjaðu á eftirfarandi þremur atriðum:

- *Sætatölur.* Skoðaðu meðaltöl og staðalfrávik heildarsæta. Brot í meðaltali
  merkir ekki að broti úr sæti hafi verið úthlutað í einstakri hermun.
- *Mismunur milli kerfa.* Skoðaðu samanburð þeirra bæði eftir listum og eftir
  heildarsætum flokka. Þau geta gefið flokkunum sömu heildarsætatölur en skipt
  sætum þeirra ólíkt milli kjördæma. Í summu algilda sætamunar telur ein
  tilfærsla frá A til B tvö: eitt sæti tapast og annað bætist við.
- *Frávik frá sætishlutum.* Skoðaðu einn eða tvo mælikvarða í þessum flokki
  áður en þú skoðir þá alla. Lægra frávik er betra samkvæmt viðkomandi mælikvarða;
  það eitt gerir kerfi ekki almennt betra.

*Kvörðun viðmiða og samanburður við annað kerfi eru ólíkir hlutir.* Kvörðunin
ákveður þá brotnu sætishluti sem ákveðnir gæðamælikvarðar bera úthlutuð sæti
saman við. Hún breytir ekki úthlutun sætanna. Sjálfgefna kvörðunin í dæminu
tekur bæði mið af heildarsætatölum kjördæma og landsfylgi flokka. Aðrar
kvörðunarleiðir leggja áherslu á annað þessara atriða. Valið þarf að hæfa því
sem þú vilt rannsaka.
Valin samanburðarkerfi eru hins vegar notuð til að bera saman sjálfar
heiltöluúthlutanirnar.

*Óvissa í meðaltali er ekki dreifing niðurstaðna.* Staðalfrávikið lýsir
breytileika milli hermdra kosninga. Bilið við meðaltalið er áætlað 95%
öryggisbil fyrir meðaltalið og þrengist að jafnaði þegar hermunum fjölgar.
Það er ekki bil sem inniheldur 95% allra hermdra úrslita. Fjölga má hermunum
enn frekar þegar meta á mun milli kerfa nánar.

Stillingin *Simulate with thresholds?* skiptir máli við samanburð kerfa með
þröskulda. Valið *No* gerir kleift að skoða kerfin án stökka sem verða
þegar flokkur fer yfir eða undir þröskuld. Það slekkur á þröskuldum og öðrum
hæfisskilyrðum flokka, nema *Stand in all constituencies*. Niðurstöðurnar
lýsa þá ekki lengur kerfunum með öllum upphaflegum skilyrðum þeirra.

Helstu niðurstöður sjást á vefsíðunni. *Download Excel file* á niðurstöðuflipunum
gefur ítarlegri töflur til skoðunar og frekari úrvinnslu. Til dæmis má finna
viðmiðunarsætishlutina í Excel-skrá hermunar. Í *Settings* má velja talnasnið
og fjölda aukastafa; það breytir framsetningu en ekki útreikningunum.

\newpage

## Eigin gögn og aðrar tilraunir

*Atkvæðagögn og kosningalög eru valin hvort í sínu lagi.* *Use preset* á
fyrsta flipanum sækir atkvæði og sætaskipan. *Election-law preset* á öðrum
flipanum stillir reglurnar en breytir ekki atkvæðum eða sætafjölda. Þannig má
bæði endurgera kosningar samkvæmt lögum viðkomandi lands og prófa önnur kerfi
á sömu úrslitum. Fyrir endurgerð raunverulegra kosninga þarf að velja bæði
viðeigandi gögn og rétta lagafyrirmynd.

Atkvæðatöflunni má breyta beint eða lesa hana úr Excel- eða CSV-skrá með
*Upload from file*. Auðveld leið til að útbúa eigin skrá er að hlaða niður
atkvæðatöflu úr herminum, breyta henni og hlaða henni inn aftur. Þá þarf ekki
að smíða skráarsniðið frá grunni.

Við stærri tilraunir getur verið gagnlegt að fækka smáflokkum með *Prune small
parties*. Aðgerðin breytir atkvæðatöflunni og fjarlægðir flokkar fá ekki sæti.
Atkvæði þeirra varðveitast í *Pruned* og eru áfram talin með þegar
atkvæðahlutföll fyrir þröskulda eru reiknuð. Vistaðu gögnin fyrst ef þú vilt
geta snúið aftur til óstyttu töflunnar.

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
