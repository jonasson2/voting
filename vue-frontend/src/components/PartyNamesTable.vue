<template>
  <div>
    <b-row>
      <b-col cols="auto">
        <legend style="margin-left:0px; margin-top:12px">Party names</legend>
      </b-col>
    </b-row>
    <div class="table-scroll">
      <table v-if="showTable" class="votematrix party-names-table">
        <thead>
          <tr>
            <th>Abbreviation</th>
            <th>Name</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(party, partyIndex) in voteTable.parties" :key="partyIndex">
            <td class="displaycenter">{{ party }}</td>
            <td>
              <input
                v-model="voteTable.party_names[partyIndex]"
                type="text"
                :size="Math.min(Math.max(voteTable.party_names[partyIndex].length + 1, 3), 50)"
                />
            </td>
          </tr>
        </tbody>
      </table>
      <table v-else class="votematrix party-names-table">
        <tbody>
          <tr>
            <th class="growtable">
              <b-button
                size="sm"
                v-b-tooltip.hover.right.v-primary.ds500
                title="Add party names"
                @click="$emit('add')"
                ><b>+</b></b-button>
            </th>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    voteTable: {type: Object, required: true},
    showTable: {type: Boolean, required: true},
  },
  emits: ["add"],
}
</script>
