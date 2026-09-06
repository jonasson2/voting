<template>
  <div>
    <b-row>
      <b-col cols="auto">
        <legend
          style="margin-left:0px; margin-top:12px"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title='Seat numbers and votes for the national list (German "Zweitstimmen", New Zealand "party votes").'
          >
          National party votes and seats
        </legend>
      </b-col>
    </b-row>
    <div class="table-scroll">
      <table class="votematrix">
        <tbody>
          <tr v-if="info.specified" size="sm">
            <th class="topleft"></th>
            <th
              class="seatnumberheading"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title='National fixed seats, allocated according to the national party votes using the fixed seat allocation rules set in the "Electoral systems" tab. Normally there are no national fixed seats, but if specified then the national party votes must not be left blank.'
              >
              # Fixed
            </th>
            <th
              class="seatnumberheading"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="National adjustment seats. These are allocated last, by filling each party's remaining seats after the allocation of all other seats (no votes are used for this allocation)"
              >
              # Adj.
            </th>
            <th
              v-for="(party, partyIndex) in voteTable.parties"
              :key="partyIndex"
              class="displaycenter"
              >
              {{ party }}
            </th>
            <th
              v-if="hasPrunedVotes"
              class="displaycenter"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Votes removed by pruning. Included only in percentage-threshold totals."
              >
              Pruned
            </th>
            <th class="displaycenter">Total</th>
          </tr>
          <tr v-if="info.specified" size="sm">
            <th class="constname">
              <b-button
                style="padding: 0"
                size="sm"
                variant="link"
                v-b-tooltip.hover.bottom.v-primary.ds500
                title="Remove party votes"
                @click="$emit('remove')"
                >X</b-button>
              <input
                v-model="info.name"
                type="text"
                v-autowidth="{ maxWidth: '400px', minWidth: '25px' }"
                />
            </th>
            <td class="numerical" size="sm">
              <input
                v-model.number="info.num_fixed_seats"
                type="text"
                v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
                />
            </td>
            <td class="numerical" size="sm">
              <input
                v-model.number="info.num_adj_seats"
                type="text"
                v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
                />
            </td>
            <td
              v-for="(party, partyIndex) in voteTable.parties"
              :key="partyIndex"
              class="numerical"
              >
              <input
                v-model.number="info.votes[partyIndex]"
                type="text"
                v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
                />
            </td>
            <td v-if="hasPrunedVotes" class="displayright">{{ info.pruned }}</td>
            <td class="displayright">{{ info.total }}</td>
          </tr>
          <tr v-if="!info.specified">
            <th class="growtable">
              <b-button
                size="sm"
                v-b-tooltip.hover.right.v-primary.ds500
                title="Add party votes"
                @click="$emit('add')"
                ><b>+</b></b-button>
            </th>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="info.specified" class="settings-row party-vote-basis-row">
      <label class="settings-field">
        <span>Votes used as basis for party totals</span>
        <b-form-select
          v-model="voteTable.party_vote_basis"
          class="compact-select settings-vote-basis"
          :options="basisOptions"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="The total number of seats for each party is computed using the votes selected here."
          />
      </label>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    voteTable: {type: Object, required: true},
    basisOptions: {type: Array, required: true},
    hasPrunedVotes: {type: Boolean, required: true},
  },
  emits: ["add", "remove"],
  computed: {
    info() {
      return this.voteTable.party_vote_info
    },
  },
}
</script>
