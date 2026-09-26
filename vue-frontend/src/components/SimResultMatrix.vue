<template>
  <b-container fluid>
    <div class="table-scroll">
    <table class="resultmatrix" style="margin-bottom:0px; font-size:90%">
      <tbody>
      <tr v-if="title">
        <th class="topleft"></th>
        <th :colspan="stddev ? 2 * parties.length + 1 : parties.length + 1"
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
            {{ format(values[conidx][partyidx]) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ format(stddev[conidx][partyidx]) }}
          </td>
        </template>
        <td class="displayright">
          {{ format(values[conidx][parties.length]) }}
        </td>
      </tr>
      <tr>
        <th class="displayleft">Total</th>
        <template v-for="(party, partyidx) in parties">
          <td class="displayright">
            {{ format(values[constituencies.length][partyidx]) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ format(stddev[constituencies.length][partyidx]) }}
          </td>
        </template>
        <td class="displayright">
          {{ format(values[constituencies.length][parties.length]) }}
        </td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">
          {{ party_votes_name }}
        </th>
        <template v-for="(party, partyidx) in parties">
          <td class="displayright">
            {{ format(values[constituencies.length + 1][partyidx]) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ format(stddev[constituencies.length + 1][partyidx]) }}
          </td>
        </template>
        <td class="displayright">
          {{ format(values[constituencies.length + 1][parties.length]) }}
        </td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">
          Grand total
        </th>
        <template v-for="(party, partyidx) in parties">
          <td class="displayright">
            {{ format(values[constituencies.length + 2][partyidx]) }}
          </td>
          <td v-if="stddev" class="displayright">
            {{ format(stddev[constituencies.length + 2][partyidx]) }}
          </td>
        </template>
        <td class="displayright">
          {{ format(values[constituencies.length + 2][parties.length]) }}
        </td>
      </tr>
      </tbody>
    </table>
    </div>
  </b-container>
</template>
<script>
import { mapState } from "vuex"
import { formatNumber } from "../numberFormat.js"

export default {
  props: {
    "constituencies": { default: [] },
    "parties": { default: [] },
    "values": { default: [] },
    "round": { default: 0 },
    "stddev": { default: false },
    "title": { default: "" },
    "party_votes_specified": false,
    "party_votes_name": "",
  },
  computed: mapState(["display_settings"]),
  methods: {
    format(value) {
      return formatNumber(value, this.round, this.display_settings)
    },
  },
}
</script>
