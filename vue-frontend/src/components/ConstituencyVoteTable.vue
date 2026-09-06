<template>
  <div class="table-scroll">
    <table class="votematrix">
      <tbody>
        <tr>
          <th class="topleft"></th>
          <th
            class="seatnumberheading"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Fixed seats"
            >
            # Fixed
          </th>
          <th
            class="seatnumberheading"
            v-b-tooltip.hover.bottom.v-primary.ds500
            :title="hasMaximums ? 'Minimum adjustment seats' : 'Adjustment seats'"
            >
            {{ hasMaximums ? '# Min adj.' : '# Adj.' }}
            <b-button
              v-if="!hasMaximums"
              class="xbutton split-adjustment-button"
              style="padding: 0; margin-left: 2px"
              size="sm"
              variant="link"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Split adjustment seats into minimum and maximum seats"
              @click="$emit('add-maximums')"
              >+
            </b-button>
          </th>
          <th
            v-if="hasMaximums"
            class="seatnumberheading"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Maximum adjustment seats"
            >
            # Max adj.
            <b-button
              class="xbutton"
              style="padding: 0; margin-left: 2px"
              size="sm"
              variant="link"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Remove maximum adjustment-seat constraints; retain the minimum as the exact number of adjustment seats"
              @click="$emit('remove-maximums')"
              >X
            </b-button>
          </th>
          <th
            v-for="(party, partyIndex) in voteTable.parties"
            :key="partyIndex"
            class="partyname"
            >
            <b-button
              class="xbutton"
              style="padding: 0"
              size="sm"
              variant="link"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Remove Party"
              @click="$emit('remove-party', partyIndex)"
              >X</b-button>
            <input
              v-model="voteTable.parties[partyIndex]"
              type="text"
              style="text-align: center"
              v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
              />
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
          <th class="growtable">
            <b-button
              size="sm"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Add party"
              @click="$emit('add-party')"
              ><b>+</b></b-button>
          </th>
        </tr>
        <tr
          v-for="(constituency, constituencyIndex) in voteTable.constituencies"
          :key="constituencyIndex"
          size="sm"
          >
          <th class="constname">
            <b-button
              style="padding: 0"
              size="sm"
              variant="link"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Remove constituency"
              @click="$emit('remove-constituency', constituencyIndex)"
              >X</b-button>
            <input
              v-model="constituency.name"
              type="text"
              v-autowidth="{ maxWidth: '400px', minWidth: '25px' }"
              />
          </th>
          <td class="numerical" size="sm">
            <input
              v-model.number="constituency.num_fixed_seats"
              type="text"
              v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
              />
          </td>
          <td class="numerical" size="sm">
            <input
              v-model.number="constituency.num_adj_seats"
              type="text"
              v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
              />
          </td>
          <td v-if="hasMaximums" class="numerical" size="sm">
            <input
              v-model.number="constituency.max_adj_seats"
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
              v-model.number="voteTable.votes[constituencyIndex][partyIndex]"
              type="text"
              v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
              />
          </td>
          <td v-if="hasPrunedVotes" class="displayright">
            {{ voteTable.pruned[constituencyIndex] }}
          </td>
          <td class="displayright">{{ voteSums.row[constituencyIndex] }}</td>
        </tr>
        <tr>
          <th class="displayleft">Total</th>
          <td class="displayright">{{ voteSums.cseats }}</td>
          <td class="displayright">{{ voteSums.aseats }}</td>
          <td v-if="hasMaximums" class="numerical">
            <input
              v-model.number="voteTable.max_total_adj_seats"
              type="text"
              v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Maximum total number of adjustment seats"
              />
          </td>
          <td
            v-for="(party, partyIndex) in voteTable.parties"
            :key="partyIndex"
            class="displayright"
            >
            {{ voteSums.col[partyIndex] }}
          </td>
          <td v-if="hasPrunedVotes" class="displayright">{{ voteSums.pruned }}</td>
          <td class="displayright">{{ voteSums.tot }}</td>
        </tr>
        <tr>
          <th class="displayleft">Vote share</th>
          <td></td>
          <td></td>
          <td v-if="hasMaximums"></td>
          <td
            v-for="(party, partyIndex) in voteTable.parties"
            :key="partyIndex"
            class="displayright"
            >
            {{ votePercentage(voteSums.col[partyIndex]) }}
          </td>
          <td v-if="hasPrunedVotes" class="displayright">
            {{ votePercentage(voteSums.pruned) }}
          </td>
          <td class="displayright">{{ votePercentage(voteSums.tot) }}</td>
        </tr>
        <tr>
          <th class="growtable">
            <b-button
              size="sm"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Add constituency"
              @click="$emit('add-constituency')"
              ><b>+</b></b-button>
          </th>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: {
    voteTable: {type: Object, required: true},
    voteSums: {type: Object, required: true},
    hasMaximums: {type: Boolean, required: true},
    hasPrunedVotes: {type: Boolean, required: true},
  },
  emits: [
    "add-constituency",
    "add-maximums",
    "add-party",
    "remove-constituency",
    "remove-maximums",
    "remove-party",
  ],
  methods: {
    votePercentage(votes) {
      const total = this.voteSums.tot
      if (!Number.isFinite(votes) || !Number.isFinite(total) || total <= 0) {
        return "–"
      }
      return (100 * votes / total).toFixed(1) + "%"
    },
  },
}
</script>
