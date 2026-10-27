# Adjustment seats and levelling: country survey

Recovered on 24 October 2026 from our investigation of 20 October 2026, with
the Nordic systems added from the existing simulator notes. This preserves
the findings and source links from that investigation; it is not a fresh
review of changes to electoral law.

## Scope and meaning

The scope is national parliamentary elections, normally the lower house.
Regional and municipal systems are excluded. The list records the countries
we examined, rather than claiming to be a complete worldwide inventory.

Here **levelling** means correcting party totals after geographical or
single-member allocations, or fitting geographical allocations to an overall
proportional party entitlement. A separate proportional tier does not qualify
if its seats are allocated independently of the constituency results.

Two operations should be distinguished:

1. Determine how many seats each party receives overall.
2. Decide where those seats go: constituency lists, regional lists, or a
   national list.

Only the second operation directly corresponds to the simulator's
adjustment-seat allocation-method selector. National-list compensation can
avoid the constituency-placement problem altogether.

## Countries with levelling or a related reconciliation

| Country | Form | Basic description |
|---|---|---|
| Austria | Higher-tier compensation | Regional, state and national allocation stages. The final national D'Hondt calculation takes account of seats already allocated; the remaining mandates are filled from federal party lists. [Interior Ministry](https://www.bmi.gv.at/412/nationalratswahlen/index.html). |
| Bulgaria | National reconciliation; no separate adjustment-seat pool | National party entitlements use Hare quota and largest remainders. Provisional constituency allocations are corrected using remainders until party and constituency totals agree. [Election Code, Annex 1](https://www.cik.bg/upload/64149/ELECTION_CODE.pdf). |
| Czechia | National second allocation stage | Seats left after constituency allocation are allocated nationally using pooled vote remainders and a quota. Each party's additional seats are placed where it has the largest absolute constituency vote remainders. [Official 2025 calculation guide](https://csu.gov.cz/docs/107516/45be1987-1275-2f2e-b642-bd6c432a92fd/rozdelovanimandatups25_popis.pdf?version=1.1). |
| Denmark | Adjustment seats, with regional constraints | National party entitlements determine each party's shortfall after fixed seats. Adjustment seats are placed first among regions using Sainte-Laguë quotients, then among constituencies within each region using Danish divisors, 1, 4, 7, etc. Regional adjustment-seat totals are prescribed; constituency totals are flexible. [Ministry's electoral-system description](https://www.elections.im.dk/media/40794/the-electoral-system-in-denmark.pdf). |
| Estonia | National compensation mandates | Seats not allocated as personal or district mandates are distributed from national lists using modified D'Hondt, accounting for seats already won. [Election authority](https://www.valimised.ee/en/estonian-elections-nutshell/ascertaining-results/ascertaining-election-results-riigikogu-elections). |
| Germany | Overall proportional allocation with constituency and list representation | Second votes determine party entitlements, which are distributed among state lists using Sainte-Laguë. Under the system used from 2025, a constituency victory needs sufficient second-vote coverage. This differs from the former overhang-and-balancing-seat system. [Federal Returning Officer: system](https://www.bundeswahlleiterin.de/en/service/glossar/w/wahlsysteme.html), [seat distribution](https://www.bundeswahlleiterin.de/en/service/glossar/s/sitzverteilung.html). |
| Iceland | Adjustment seats with fixed constituency counts | National party entitlements determine adjustment-seat claims. Parties receive adjustment seats in a national sequence; each seat goes to an eligible constituency list using its next D'Hondt quotient divided by total constituency votes, subject to constituency capacity. [Elections Act, Article 110](https://www.althingi.is/lagas/nuna/2021112.html). |
| New Zealand | National list top-up seats | Sainte-Laguë determines overall party entitlements from the party vote. Electorate seats are deducted, and the remaining entitlement is filled from national party lists, subject to the system's overhang provisions. [Electoral Commission](https://elections.nz/democracy-in-nz/what-is-new-zealands-system-of-government/how-are-mps-elected/). |
| Norway | Adjustment seats with fixed constituency counts | National party entitlements determine shortfalls after fixed seats. Placement uses a party's next Sainte-Laguë quotient weighted by the constituency's fixed seats divided by its total votes. [Electoral Directorate's 2025 allocation report](https://www.valg.no/globalassets/dokumenter-2025/utjevningsmandater-2025.pdf). |
| Romania | National redistribution of unused votes | Initial constituency quota allocations leave unused votes and unfilled seats. National D'Hondt distributes the remaining seats using unused votes. A separate procedure places them geographically using normalized unused-vote claims, constituency capacities and correction rules. [Election law, Article 94](https://legislatie.just.ro/public/detaliidocument/170037). |
| Slovenia | National compensation placed among constituency lists | National D'Hondt determines party entitlements after accounting for constituency seats. Additional seats go to constituency lists according to remaining votes divided by the constituency quota, skipping full constituencies. [Government description](https://www.gov.si/en/topics/elections-to-the-national-assembly/), [Election Act, Article 93](https://pisrs.si/api/datoteke/integracije/355436025). |
| South Africa | National compensatory seats | Regional allocations are supplemented by national compensatory seats to obtain overall party proportionality. The compensatory seats come from national lists. [Electoral Commission](https://www.elections.org.za/pw/elections/whats-new-in-the-2024-elections-electoral-amendment-act). |
| Sweden | Flexible constituency adjustment seats | National party entitlements determine shortfalls after fixed-seat reconciliation. Each party's adjustment seats go where its next ordinary Sainte-Laguë quotients are highest; there are no prescribed adjustment-seat counts per constituency. [Election Authority](https://www.val.se/det-svenska-valsystemet/rostrakning-och-mandatfordelning/sa-fordelas-mandaten). |
| Uruguay | Complementary allocation among departments | After initial departmental allocations, complementary seats correct national party totals. Placement uses party votes in a department divided by its seats already there plus one, with party and departmental limits and statutory corrections. [Election law, Articles 5–9](https://www.impo.com.uy/bases/leyes-corte-electoral-nd/7912-1925), especially [Article 9](https://www.impo.com.uy/bases/leyes-corte-electoral-nd/7912-1925/9). |

## Other countries examined: no levelling tier in the system described

“No” here does not imply that proportional representation is absent. Some
systems allocate all seats proportionally from the outset; others have
separate geographical allocations or parallel electoral tiers.

| Country | Basic arrangement and reason for exclusion |
|---|---|
| Argentina | D'Hondt within provinces and Buenos Aires city, without national compensation. [Official electoral-system guide](https://www.argentina.gob.ar/sites/default/files/2024/08/libro_sistema_electoral_argentino.pdf). |
| Belgium | Federal Chamber seats are allocated within constituencies using D'Hondt, without national compensation. [Federal election authority](https://elections.fgov.be/informations-generales-depouillement-repartition-des-sieges-et-designation-des-elus/chambre-des). |
| Brazil | Federal deputy seats are allocated within states and the Federal District. Remaining-seat procedures complete those allocations rather than correcting national party totals. [Electoral Court](https://www.tse.jus.br/comunicacao/noticias/2023/Julho/quocientes-eleitoral-partidario-e-sobras-por-media-entenda-como-funcionam-esses-calculos-eleitorais). |
| Chile | D'Hondt within constituencies, including allocation within electoral alliances; no national adjustment tier. [Electoral Service](https://www.servel.cl/metodo-dhondt/). |
| France | Two-round elections in single-member constituencies; no proportional top-up tier. [National Assembly](https://www2.assemblee-nationale.fr/qui/les-elections-legislatives). |
| India | Single-member plurality elections to the Lok Sabha; no adjustment tier. [Election Commission](https://www.eci.gov.in/EBooks/eci-atlas/files/basic-html/page104.html). |
| Indonesia | Sainte-Laguë within constituencies for the national DPR; no national adjustment tier. [Election Commission explanation](https://kab-klungkung.kpu.go.id/blog/read/andre-sainte-lague-dan-kursi-parlemen). |
| Italy | Under Rosatellum, single-member and proportional seats are allocated separately. Geographical corrections within the proportional component do not compensate for disproportionality in the single-member component. [Chamber of Deputies](https://temi.camera.it/leg19DIL/temi/19_tl18_riforma_elettorale.html). |
| Japan | Single-member seats and regional proportional seats are parallel components; the proportional seats do not compensate for constituency victories. [Official election explanation](https://www.city.fukuoka.lg.jp/senkan/senkyo/shisei/senkyo_kiso/senkyo_kiso_syurui.html). |
| Latvia | Sainte-Laguë within five constituencies, without national compensation. [Election law, Section 38](https://likumi.lv/ta/en/en/id/35261-law-on-the-election-of-the-isaeimai). |
| Lithuania | Single-member and national proportional components are separate; constituency victories are not deducted from party-list entitlements. [Electoral Code](https://e-seimas.lrs.lt/portal/legalActPrint/lt?category=TAD&documentId=28a7cbf395fb11ef955ff95815eb5ce5). |
| Netherlands | Seats are allocated from national party totals from the outset. Remaining-seat allocation handles rounding rather than compensation for earlier geographical allocations. [Electoral Council](https://www.kiesraad.nl/verkiezingen/tweede-kamer/uitslagen/zetelverdeling-over-partijen). |
| Poland | Sejm seats are allocated within constituencies; no national adjustment tier in the system examined. [National Electoral Commission account](https://www.pkw.gov.pl/uploaded_files/1488880447_KBW_25lecie-2-www.pdf). |
| Portugal | D'Hondt within constituencies, without national compensation. [Parliament](https://www.parlamento.pt/sites/EN/Parliament). |
| Serbia | Examined for its weighting of qualifying minority lists' D'Hondt quotients, rather than as a geographical levelling system. The minority-list weighting is not an adjustment-seat tier. [Election Act, Article 140](https://www.rik.parlament.gov.rs/extfile/en/1638/Zakon%20o%20izboru%20narodnih%20poslanika_ENGLESKI-ociscen%20final.pdf). |
| Slovakia | A single nationwide constituency with quota and remainder allocation; no separate geographical compensation stage. [Statistical Office](https://volby.statistics.sk/nrsr/nrsr2023/en/mandaty_strany.html). |
| Spain | Congress seats are allocated within provincial constituencies, principally using D'Hondt, without national compensation. [Congress](https://blog.congreso.es/sistema-electoral/). |
| Switzerland | National Council seats are allocated within cantons, without national compensation. This finding concerns federal elections, not cantonal systems. [Federal Constitution](https://www.parlament.ch/centers/documents/en/20220228_BV-en.pdf). |
| Taiwan | Constituency and national party-list seats are parallel components; list seats do not compensate for constituency results. [Central Election Commission](https://web.cec.gov.tw/central/article/20162). |

## Main findings for the simulator

- **National party apportionment and geographical placement are different
  choices.** Use of D'Hondt or Sainte-Laguë nationally does not establish that
  the placement stage uses the same rule.
- **Denmark, Sweden and Uruguay** provide geographically distributed
  next-quotient allocation procedures. Their capacities, divisor rules and
  other legal provisions differ; they are not identical systems.
- **Iceland and Norway** normalize geographical placement scores by
  constituency votes; Norway additionally weights by fixed seats.
- **Slovenia and Czechia** illustrate placement by relative and absolute vote
  remainders, respectively. Czechia's initial constituency quota is Imperiali,
  `eligible votes / (constituency seats + 2)`, not Hare. Its national second
  stage uses a different quota. Imperiali quota must not be confused with
  the Imperiali divisor method.
- **Romania** uses unused votes and a distinct normalized placement procedure,
  rather than simply choosing the largest next-seat quotient.
- **Bulgaria** illustrates reconciliation of national and constituency totals
  without a predetermined pool of adjustment seats.
- Several compensatory systems use **national lists**, so they offer no
  direct alternative rule for placing a party's adjustment seats among
  constituencies.

For fuller Nordic implementation details, see
[the Danish discussion](danish-discussion.txt),
[the Swedish discussion](swedish-discussion.txt), and
[the agreed method terminology](terminology.md#allocation-method-names).
