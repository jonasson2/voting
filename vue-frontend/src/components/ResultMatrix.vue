<template>
<b-container fluid>
  <div class="table-scroll">
    <table class="resultmatrix" style="margin-bottom:0px">
      <tbody>
      <tr>
        <th class="topleft"></th>
        <th v-for="(party, partyidx) in parties" class="displaycenter">
          {{parties[partyidx]}}
        </th>
        <th class="displaycenter">
          Total
        </th>
        <th class="displaycenter"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Total constituency votes, including pruned votes, divided by final seats (fixed and adjustment).">
          Votes per seat
        </th>
      </tr>
      <tr v-for="(constituency, conidx) in constituencies">
        <th class="displayleft">
          {{ constituency["name"] }}
        </th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
            {{ format(values[conidx][partyidx - 1]) }}
          </td>
        </template>
        <td class="displayright">{{ formatVotesPerSeat(votes_per_seat[conidx]) }}</td>
      </tr>
      <tr>
        <th class="displayleft">Total</th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
            {{ format(values[constituencies.length][partyidx - 1]) }}
          </td>
        </template>
        <td class="displayright">{{ formatVotesPerSeat(votes_per_seat[constituencies.length]) }}</td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">
          {{ party_votes_name }}
        </th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
            {{ format(values[constituencies.length + 1][partyidx - 1]) }}
          </td>
        </template>
        <td class="displayright">–</td>
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">Grand total</th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
            {{ format(values[constituencies.length + 2][partyidx - 1]) }}
          </td>
        </template>
        <td class="displayright">–</td>
      </tr>
      </tbody>
    </table>
  </div>
  <p style="margin:5px 0px 0px; font-size:90%">
    The table shows total seats including adjustment seats (in brackets).
  </p>
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
    "votes_per_seat": { type: Array, default: () => [] },
    "party_votes_specified": false,
    "party_votes_name": "",
  },
  computed: mapState(["display_settings"]),
  methods: {
    formatVotesPerSeat(value) {
      return Number.isFinite(value)
        ? formatNumber(value, this.display_settings.fractional_digits, this.display_settings)
        : "–"
    },
    format(value) {
      return typeof value === "number"
        ? formatNumber(value, 0, this.display_settings)
        : value
    },
  },
}
</script>
