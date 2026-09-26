# Bráðabirgðaefni fyrir dæmi 3: Svíþjóð

Áætlunin og textadrögin hér að neðan eru til bráðabirgða fyrir þriðju tilraunina.
Þau þarf að yfirfara áður en þau fara aftur í leiðbeiningarnar.

## Fyrri áætlun

Næsta tilraun notar nýjustu sænsku kosningarnar. Hún færir lesandann frá litla
2×2 dæminu yfir í raunveruleg gögn og flóknara kosningakerfi, án þess að verða
að tæmandi lýsingu á sænsku kosningalögunum.

Í kaflanum mætti fjalla um eftirfarandi atriði í þessari röð:

1. Velja nýjustu sænsku kosningaúrslitin úr tilbúnum gögnum hermisins.
2. Skoða hvernig lágmark og hámark jöfnunarsæta í kjördæmum eru skráð. Í
   sænska kerfinu er lágmarkið núll, hámarkið ótakmarkað og heildarfjöldi
   jöfnunarsæta tilgreindur sérstaklega.
3. Fækka smáflokkum með *Prune small parties* og útskýra að atkvæði þeirra
   varðveitast í *Pruned* og teljast áfram með við útreikning þröskulda.
4. Velja sænsku kosningalagafyrirmyndina og reikna úthlutunina.
5. Útskýra í stuttu máli hlutverk *Swedish switching*: fyrst eru föst sæti
   borin saman við landsúthlutun flokkanna og hugsanleg umframsæti færð áður
   en jöfnunarsætum er úthlutað.
6. Búa til annað kerfi á sömu gögnum og bera sænsku aðferðina saman við aðra
   aðferð við staðsetningu jöfnunarsæta, til dæmis *Maximum constituency vote
   percentage*.
7. Benda á að til að fá dæmi þar sem "Swedish switchint" skipti raunverulega á
   einhverjum sætum megi beita 2018+ lögum á kosningarnar frá 2014.

Kaflinn ætti að halda sama stutta og tilraunamiðaða sniði og 2×2 dæmið. Ekki
þarf að útskýra alla stærðfræðina þar; ítarleg lýsing á úthlutunarreglum á
heima í sérstöku stærðfræðiskjali.

## Bráðabirgðadrög: sænsku kosningarnar 2026

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
