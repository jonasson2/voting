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
      </tr>
      <tr v-for="(constituency, conidx) in constituencies">
        <th class="displayleft">
          {{ constituency["name"] }}
        </th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
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
      </tr>
      <tr v-if="party_votes_specified">
        <th class="displayleft">Grand total</th>
        <template v-for="partyidx in parties.length + 1">
          <td class="displaycenter">
            {{ values[constituencies.length + 2][partyidx - 1] }}
          </td>
        </template>
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

export default {
  props: {
    "constituencies": { default: [] },
    "parties": { default: [] },
    "values": { default: [] },
    "party_votes_specified": false,
    "party_votes_name": "",
  },
}
</script>
