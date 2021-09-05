<template>
  <b-container fluid>
    <table class="resultmatrix" v-if="values.length > 0">
      <tr v-if="title">
        <th class="topleft"></th>
        <th :colspan="stddev?2*parties.length:parties.length">
          {{title}}
        </th>
      </tr>
      <tr>
        <th class="topleft"></th>
        <th class="displaypartyname"
          :colspan="stddev?2:1"
          v-for="(party, partyidx) in parties"
        >
          {{parties[partyidx]}}
        </th>
      </tr>
      <tr v-if="stddev" class="parties">
        <th class="topleft"></th>
        <template v-for="(party, partyidx) in parties">
          <td class="partyseats">Average</td>
          <td class="partyseats">Stddev</td>
        </template>
      </tr>
      <tr v-for="(constituency, conidx) in constituencies">
        <th class="constname">
          {{ constituency["name"] }}
        </th>
        <template v-for="(party, partyidx) in parties">
          <td class="partyseats">
            {{ values[conidx][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="partyseats">
            {{ stddev[conidx][partyidx].toFixed(round) }}
          </td>
        </template>
      </tr>
      <tr>
        <th class="constname">Total</th>
        <template v-for="(party, partyidx) in parties">
          <td class="partyseats">
            {{ values[constituencies.length][partyidx].toFixed(round) }}
          </td>
          <td v-if="stddev" class="partyseats">
            {{ stddev[constituencies.length][partyidx].toFixed(round) }}
          </td>
        </template>
      </tr>
    </table>
  </b-container>
</template>
<script>
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
