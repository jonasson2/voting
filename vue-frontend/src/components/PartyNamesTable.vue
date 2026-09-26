<template>
  <div>
    <b-row>
      <b-col cols="auto">
        <legend class="vote-table-section-heading">Party names</legend>
      </b-col>
    </b-row>
    <div class="table-scroll">
      <table v-if="showTable" class="votematrix party-names-table"
        v-grid-navigation="'vertical'">
        <thead>
          <tr>
            <th>Abbreviation</th>
            <th>Name</th>
            <th v-b-tooltip.hover.top.v-primary.ds500
              title="A single candidate may have votes in only one constituency and receive at most one fixed seat, but no adjustment or national seats. Single candidates are excluded from simulations; their votes remain in threshold totals. In Denmark they are called independents.">
              Single candidate
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(party, partyIndex) in voteTable.parties" :key="partyIndex">
            <td class="displaycenter">{{ party }}</td>
            <td>
              <input
                v-model="voteTable.party_names[partyIndex]"
                type="text"
                :data-grid-row="partyIndex"
                data-grid-column="0"
                :size="Math.min(Math.max(voteTable.party_names[partyIndex].length + 1, 3), 50)"
                />
            </td>
            <td class="displaycenter">
              <input type="checkbox" v-model="voteTable.independent_candidates[partyIndex]"
                :data-grid-row="partyIndex" data-grid-column="1"
                :aria-label="`${party}: single candidate`" />
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
                ><span class="add-button-symbol">+</span></b-button>
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
