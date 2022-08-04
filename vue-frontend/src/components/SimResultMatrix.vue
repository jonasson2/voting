<template>
  <b-container fluid>
    <table class="resultmatrix" style="margin-bottom:0px; font-size:90%">
      <tr v-if="title">
        <th class="topleft"></th>
        <th :colspan="stddev?2*parties.length:parties.length"
            class="displaycenter">
          {{title}}
        </th>
      </tr>
      <tr>
        <th class="topleft"></th>
        <th v-for="(party, partyidx) in parties"
            class="displaycenter"
            :colspan="stddev?2:1"
            >
          {{parties[partyidx]}}
        </th>
        <th class="displaycenter">
          Total
        </th>
      </tr>
      <tr v-if="stddev">
        <th class="topleft"></th>
        <template v-for="(party, partyidx) in parties">
          <th style="text-align:center">Avg.</th>
          <th style="text-align:center">SD</th>
        </template>
        <td></td>
      </tr>
      <tr v-for="(constituency, conidx) in constituencies">
        <th class="displayleft">
          {{ constituency["name"] }}
        </th>
        <template v-for="(party, partyidx) in parties">
          <Td v-if="voteless && voteless[conidx][partyidx]" class="red displayright">
            {{ values[conidx][partyidx].toFixed(round) }}
          </td>
          <td v-else class="displayright">
            {{ values[conidx][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ stddev[conidx][partyidx].toFixed(round) }}
          </td>
        </template>
        <td class="displayright">
          {{ values[conidx][parties.length].toFixed(round) }}
        </td>
      </tr>
      <tr>
        <th class="displayleft">Total</th>
        <template v-for="(party, partyidx) in parties">
          <td class="displayright">
            {{ values[constituencies.length][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ stddev[constituencies.length][partyidx].toFixed(round) }}
          </td>
        </template>
        <td class="displayright">
          {{ values[constituencies.length][parties.length].toFixed(round) }}
        </td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">
          {{ party_votes_name }}
        </th>
        <template v-for="(party, partyidx) in parties">
          <td class="displaycenter">
            {{ values[constituencies.length + 1][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ stddev[constituencies.length + 1][partyidx].toFixed(round) }}
          </td>
        </template>
        <td class="displayright">
          {{ values[constituencies.length + 1][parties.length].toFixed(round) }}
        </td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">
          Grand total
        </th>
        <template v-for="(party, partyidx) in parties">
          <td class="displaycenter">
            {{ values[constituencies.length + 2][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ stddev[constituencies.length + 2][partyidx].toFixed(round) }}
          </td>
        </template>
        <td class="displayright">
          {{ values[constituencies.length + 2][parties.length].toFixed(round) }}
        </td>
      </tr>
    </table>
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
    "round": { default: 0 },
    "stddev": { default: false },
    "title": { default: "" },
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
