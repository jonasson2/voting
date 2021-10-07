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
    <tr v-if="stddev" class="parties">
      <th class="topleft"></th>
      <template v-for="(party, partyidx) in parties">
        <td class="displayright">Average</td>
        <td class="displayright">Stderr</td>
      </template>
      <td></td>
    </tr>
    <tr v-for="(constituency, conidx) in constituencies">
      <th class="displayleft">
        {{ constituency["name"] }}
      </th>
      <template v-for="(party, partyidx) in parties">
        <td class="displayright">
          {{ values[conidx][partyidx].toFixed() }}
        </td>
        <td v-if="stddev" class="displayright">
          {{ stddev[conidx][partyidx].toFixed() }}
        </td>
      </template>
      <td class="displayright">
        {{ values[conidx][parties.length].toFixed() }}
      </td>
    </tr>
    <tr>
      <th class="displayleft">Total</th>
      <template v-for="(party, partyidx) in parties">
        <td class="displayright">
          {{ values[constituencies.length][partyidx].toFixed() }}
        </td>
        <td v-if="stddev" class="displayright">
          {{ stddev[constituencies.length][partyidx].toFixed() }}
        </td>
      </template>
      <td class="displayright">
        {{ values[constituencies.length][parties.length].toFixed() }}
      </td>
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
