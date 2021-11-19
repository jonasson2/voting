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
          <td class="displayright">
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
    </table>
    <br>
  </b-container>
</template>
<script>

import { mapState } from 'vuex'  
export default {
  props: {
    "constituencies": { default: [] },
    "parties": { default: [] },
    "values": { default: [] },
    "round": { default: 0 },
    "stddev": { default: false },
    "title": { default: "" },
  }
}
</script>
