<template>
<div>
  <b-button-toolbar key-nav aria-label="Instruct">
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Short instructions in English"
        @click="leidbeiningar()"
        v-b-modal.modalpreset
        >
        Instructions
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Instructions in Icelandic"
        @click="leidbeiningar()"
        >
        Leiðbeiningar
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <b-tabs
    active-nav-item-class="font-weight-bold"
    no-key-nav card
    >
    <b-tab title="About the Election Simulator">
      <p>
      This software allows the user to design different types of electoral.
      These can be tested and compared on the basis of a multitude of randomly
      generated elections results. For each of them seats are allocated and the
      results expressed as averages together with corresponding statistics.
      Furthermore several quality measures are calculated making it possible to
      rank the election systems in terms of their qualities.</p>

      <p>
      The simulator is mainly intended for bidimensional elections, i.e.
      parlamentary elections with constituencies and parties but can also be
      used for one dimensional elections, like elections to municipalities. The
      focus is on proportional representation with multimember constituencies
      and two types of seats; pure constitency seats and adjustment seats tied
      to the constituencies. The adjusment seats can also be located nationally.
      Elections in one-man constituencies can also be addressed.</p>

      <p>
      The project has been developed in Iceland. The main contributers to the
      development of the simulator are (in alphabetic order): Martha Guðrún
      Bjarnadóttir, <a href="mailto:jonasson@hi.is">Kristján Jónasson</a> who
      supervises the development of the softwar, Pétur Ólafur Aðalgeirsson,
      Smári McCarthy and <a href="mailto:thorkellhelgason@gmail.com">Þorkell
      Helgason</a> who is responsible for the project.</p>
    </b-tab>
    <b-tab title="Um Kosningaherminn">
      <p>
      Kosningahermirinn er hugbúnaður sem gerir kleift að prófa hugmyndir um
      kjördæmaskipan og kosningakerfi. Hermirinn er hugsaður til prófunar á
      kosningakerfum eins og í kosningum til þjóðþinga. Notandinn getur hannað
      sín eigin kerfi, eitt eða fleiri, kannað eiginleika þeirra og borið þau
      saman með ýmsum gæðamæli¬kvörðum. Þingsætum má skipta að vild milli
      kjördæma og í kjördæmis- og jöfnunarsæti. Velja má á milli
      úthlutunarreglna, setja þröskulda bæði í kjördæmum og á landsvísu, en ekki
      síst prófa margvíslegar útfærslur á útdeilingu jöfnunarsæta til listanna.
      Gildandi lög um kosningar til Alþingis standa notendum til boða auk ýmissa
      tilbrigða við þau svo og hugmyndir um ný kerfi. Notandinn getur vistað
      lýsingu á kosningakerfum þeim sem hann setur saman til síðari notkunar.
      Herminn má enn fremur nota við könnun á einfaldari kerfum, svo sem við
      kosningar til sveitarstjórna.

      <h4>Aðferðafræði</h4>

      <p>Prófun kerfanna fer þannig fram að kallaðar eru fram með hermun fjölmörg
      kosningaúrslit og sætum úthlutað á grundvelli þeirra. Fjöldi hermana er að
      vali notandans. Útgangspunktur hermananna eru tiltekin kosningaúrslit,
      tilbúin eða raunveruleg, svo sem Alþingisþingkosningar á þessari öld. Slík
      grunnúrslit mynda væntigildi hinna hermdu úrslita. Tilgreina má hvað hafa
      skal mikla dreifingu á þessum tilbúnu úrslitum með því að velja
      fráviksstuðull og velja á milli nokkurra dreifireglna. Niðurstöður úr
      herminum sýna meðaltöl af úthlutun þingsæta, bæði til einstakra lista og
      til flokka, fyrir hvert þeirra kerfa sem til skoðunar er. Enn fremur fást
      staðalfrávik þessara talna svo og 95% vikmörk. Hermirinn skilar ýmsum
      mæli¬kvörðum á eiginleikum hvers prófaðs kerfis og gerir þannig kleift að
      bera þau saman. Niðurstöður birtast á vefsíðunni sjálfri en auk þess má
      hlaða niður Excel-skjali mð ítarlegri upplýsingum.</p>
      
      <h4>Markhópur</h4>
      
      <p>Hermirinn er fyrst og fremst ætlaður þeim sem kanna vilja breytt
      fyrirkaomulag þingkosninga, hvort sem það eru stjórnvöld, þingmenn,
      fræðimenn eða aðrir áhugmenn um kosningamál. Hermirinn er ekki hugsaður
      til spádóma um ókomnar kosningar en hann má þó nota til að meta líklega
      dreifingu sæta að gefinni einni eða fleiri viðhorfskönnunum.</p>

      <h4>Þróunarsagan</h4>

      <p>Hermirinn hefur verið í þróun í nokkur ár. Fjölmargir hafa komið að gerð
      hans, bæði ólaunaðir áhugamenn en líka stúdentar sem hafa haft sumarvinnu
      við forritun. Í því skyni hefur Nýsköpunarsjóður námsmanna veitt styrki.
      Enn fremur hefur dómsmálaráðuneytið, fyrir milligöngu skrifstofu Alþingis,
      greitt fyrir hálfs árs vinnu við forritun. Þeir sem mest hafa unnið að
      verkefninu eru (í stafrófsröð) <a href="mailto:jonasson@hi.is">Kristján
      Jónasson</a>, Lilja Steinunn Jónsdóttir, Martha Guðrún Bjarnadóttir, Pétur
      Ólafur Aðalgeirsson, Smári McCarthy
      og <a href="mailto:thorkellhelgason@gmail.com">Þorkell Helgason</a>, sem
      er í forsvari fyrir kosningaherminn. Kristján hefur nú umsjón með
      forritunarvinnunni. Hermirinn er enn í þróun, einkum þannig að bætt verði
      við nýjum möguleikum. Viðmót hermisins er enn aðeins á ensku en
      leiðbeiningarar eru einnig á íslensku.</p>

    </b-tab>
  </b-tabs>
</div>
</template>

<script>
  export default {
    methods: {
      leidbeiningar: function() {
        let url = "https://cs.hi.is/voting/leidbeiningar.pdf"
        window.open(url, "_blank")
      }
    }
  };
</script>
