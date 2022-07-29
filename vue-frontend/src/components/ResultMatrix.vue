<template>
<b-container fluid>
  <table class="resultmatrix" style="margin-bottom:0px">
    <tr>
      <th class="topleft"></th>
      <th v-for="(party, partyidx) in parties" class="displaycenter">
        {{parties[partyidx]}}
      </th>
      <th class="displaycenter">
        Total
      </th>
    </tr>
    <tr v-for="(constituency, conidx) in constituencies">
      <th class="displayleft">
        {{ constituency["name"] }}
      </th>
      <template v-for="partyidx in parties.length + 1">
        <td v-if="partyidx <= parties.length && voteless[conidx][partyidx-1]"
            class="red displaycenter">
          {{ values[conidx][partyidx - 1] }}
        </td>
        <td v-else class="displaycenter">
          {{ values[conidx][partyidx - 1] }}
        </td>
      </template>
    </tr>
    <tr>
      <th class="displayleft">Total</th>
      <template v-for="partyidx in parties.length + 1">
        <td class="displaycenter">
          {{ values[constituencies.length][partyidx - 1] }}
        </td>
      </template>
    </tr>
    <tr v-if="party_votes_specified">
      <th class="displayleft">
        {{ party_votes_name }}
      </th>
      <template v-for="partyidx in parties.length + 1">
        <td class="displaycenter">
          {{ values[constituencies.length + 1][partyidx - 1] }}
        </td>
      </template>
    <tr v-if="party_votes_specified">
      <th class="displayleft">Grand total</th>
      <template v-for="partyidx in parties.length + 1">
        <td class="displaycenter">
          {{ values[constituencies.length + 2][partyidx - 1] }}
        </td>
      </template>
    </tr>
</div>
</table>
<p style="margin:5px 0px 0px; font-size:90%">
    The table shows total seats including adjustments seats (in brackets).
  </p>
  <br>
  <b-alert :show="some_red" >
    The electoral system was forced to allocate some seats to lists without votes (shown in red)
  </b-alert>
</b-container>
</template>
<script>

import { mapState } from 'vuex'  
export default {
  props: {
    "constituencies": { default: [] },
    "parties": { default: [] },
    "values": { default: [] },
    "voteless": { default: null },
    "party_votes_specified": false,
    "party_votes_name": "",
  },
  computed: {
    some_red: {
      get() { 
        for (let i=0; i<this.constituencies.length; i++)
          for (let j=0; j<this.parties.length; j++) 
            if (this.voteless && this.voteless[i][j]) return true
        return false
      }
    }
  }
}
</script>
