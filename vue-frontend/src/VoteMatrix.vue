<template>
<b-container fluid class="votematrix-container">
  <b-modal
    size="lg"
    id="modalupload"
    ref="modaluploadref"
    title="Upload CSV or XLSX file"
    >
    <p>
      The first row contains the table name, seat-column headings, and party
      abbreviations. Constituency names appear in the first column.
    </p>
    <b-img rounded fluid src="static/img/parties_xlsx.png" />
    <p>
      Use <code>fixed,adj</code> for exact adjustment-seat counts, or
      <code>fixed,min_adj,max_adj</code> with a <code>Max adj seats</code> row
      for bounds. Optional <code>Party names</code> and <code>Pruned</code>
      fields are preserved.
    </p>
    <b-form-file
      v-model="uploadfile"
      accept=".csv, .xlsx"
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      @input="$refs.modaluploadref.hide();
              loadVotes();"
      ></b-form-file>
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">
        Cancel
      </b-button>
    </template>
  </b-modal>
  
  <b-modal
    size="lg"
    id="modaluploadall"
    ref="modaluploadallref"
    title="Upload json file with vote table and settings"
    >
    <p>
      The file provided should be a JSON file formatted like a file
      downloaded from here using the SAVE ALL button.
    </p>
    <b-form-file
      v-model="uploadfile"
      accept=".json"
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      @input="$refs.modaluploadallref.hide();
              loadAll();"
      ></b-form-file>
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">
        Cancel
      </b-button>
    </template>
  </b-modal>
  
  <b-modal
    size="md"
    id="modalpreset"
    ref="modalpresetref"
    title="Load preset"
    >
    <b-table
      small
      hover 
      :items="presets"
      :fields="presetfields"
      @row-clicked="loadPreset"
      >
    </b-table> 
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">
        Cancel
      </b-button>
    </template>
  </b-modal>
  
  <b-button-toolbar key-nav aria-label="Vote tools">
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Use preset votes and seat table from real or fictional elections"
        v-b-modal.modalpreset
        >
        Use preset
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Upload votes and seat table from local Excel or CSV file"
        v-b-modal.modalupload
        >
        Upload from file
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1 mb-10">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Delete votes and seat table"
        @click="clearAll()"
        >
        Delete
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download votes and seat table to local Excel xlsx-file."
        @click="save()"
        >
        Download
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Upload vote table, all electoral systems, and simulation
               settings from local JSON file."
        v-b-modal.modaluploadall
        >
        Upload all
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download vote table, all electoral systems and simulation 
               settings to local JSON file."
        @click="saveAll()"
        >
        Download all
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Remove parties whose constituency vote total is below the specified percentage of all constituency votes."
        @click="pruneSmallParties()"
        >
        Prune small parties
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <br />
  <div class="vote-table-controls">
    <label for="vote-table-name">Votes-and-seats table</label>
    <input
      id="vote-table-name"
      class="table-name-input"
      type="text"
      v-autowidth="{ maxWidth: '600px', minWidth: '25px' }"
      v-model="vote_table.name"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="The votes-and-seats table consists of the Constituency
             votes and seats, and the National party votes and seats
             (if specified)"
      />
    <label class="prune-percent-label" for="prune-small-parties-percent">Small party cutoff</label>
    <input
      id="prune-small-parties-percent"
      class="compact-entry-input prune-percent-input"
      type="text"
      v-autowidth="{ maxWidth: '70px', minWidth: '25px' }"
      v-model.number="prune_percent"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Parties with less than this percentage of all constituency votes are removed from the table."
      />
    <span class="compact-entry-unit">%</span>
  </div>
  <b-row>
    <b-col cols="auto">
      <legend
        style = "margin-left:0px"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Seat numbers and votes in each constituency.
               These, and the following national party votes and seats (if specified)
               are used as basis for allocation in the Single election tab 
               and as expected values in the Simulated elections tab"
        >
        Constituency votes and seats
      </legend>    
    </b-col>
  </b-row>
  <constituency-vote-table
    :vote-table="vote_table"
    :vote-sums="vote_sums"
    :has-maximums="hasMaxAdjustmentSeats"
    :has-pruned-votes="hasPrunedVotes"
    @add-constituency="addConstituency"
    @add-maximums="addMaximumAdjustmentSeats"
    @add-party="addParty"
    @remove-constituency="deleteConstituency"
    @remove-maximums="removeMaximumAdjustmentSeats"
    @remove-party="deleteParty"
    />
  <b-alert :show="checkVoteSeats()==false">
    Some seats are not in numerical format
  </b-alert>
  <b-alert :show="checkVoteInput()==false">
    Some votes are not in numerical format
  </b-alert>
  <b-alert :show="checkVoteLabels()==false">
    Table, party, and constituency names must not be blank
  </b-alert>
  
  
  <national-party-votes
    :vote-table="vote_table"
    :basis-options="partyVoteBasisOptions"
    :has-pruned-votes="hasPrunedVotes"
    @add="addPartyVotes"
    @remove="deletePartyVotes"
    />
  <b-alert :show="checkPartyInput()==false">
    The national name, seats, and votes must be valid
  </b-alert>

  <party-names-table
    :vote-table="vote_table"
    :show-table="showPartyNameTable"
    @add="addPartyNames"
    />
  
</b-container>
</template>

<script>
import { mapState,mapMutations,mapActions } from 'vuex';
import ConstituencyVoteTable from "./components/ConstituencyVoteTable.vue";
import NationalPartyVotes from "./components/NationalPartyVotes.vue";
import PartyNamesTable from "./components/PartyNamesTable.vue";
import {
  addAdjustmentSeatMaximums,
  addConstituency,
  addParty,
  clearVoteTable,
  pruneSmallParties,
  removeAdjustmentSeatMaximums,
  removeConstituency,
  removeParty,
  validConstituencySeats,
  validNationalVotes,
  validVoteTableLabels,
  validVotes,
} from "./voteTable.js";

export default {
  components: {
    ConstituencyVoteTable,
    NationalPartyVotes,
    PartyNamesTable,
  },
  computed: {
    ...mapState([
      'vote_table',
      'vote_sums',
      'waiting_for_data',
      'sim_capabilities',
    ]),
    partyVoteBasisOptions() {
      return this.sim_capabilities.seat_spec_options
        ? this.sim_capabilities.seat_spec_options.party
        : []
    },
    hasPrunedVotes() {
      return this.vote_table.pruned.some(value => value > 0)
        || this.vote_table.party_vote_info.pruned > 0
    },
    hasPartyNames() {
      return Array.isArray(this.vote_table.party_names)
        && this.vote_table.party_names.some(name => name.trim())
    },
    hasMaxAdjustmentSeats() {
      return this.show_max_adj_seats
    },
    showPartyNameTable() {
      return this.hasPartyNames || (this.show_party_names
        && Array.isArray(this.vote_table.party_names))
    },
  },
  data: function () {
    return {
      presets: [],
      presetfields: [
        { key: "Country", sortable: true },
        { key: "Name", sortable: true },
        { key: "Year", sortable: true },
      ],
      uploadfile: null,
      prune_percent: 1,
      show_party_names: false,
      show_max_adj_seats: false,
    };
  },
  created: function () {
    this.$http.get("api/presets/").then(
      (response) => {
        if (!response.body || response.body.error) {
          this.serverError(response.body) 
        } else {
          this.presets = response.body;
          this.updateVoteSums()
        }
      }
    )
  },
  methods: {
    ...mapMutations([
      "updateVoteSums",
      "updateVoteTable",
      "serverError",
      "setWaitingForData",
      "clearWaitingForData",
      "addBeforeunload"
    ]),
    ...mapActions([
      "saveAll",
      "downloadFile",
      "uploadAll",
    ]),
    deleteParty: function (index) {
      removeParty(this.vote_table, index)
    },
    deleteConstituency: function (index) {
      removeConstituency(this.vote_table, index)
    },
    addParty: function () {
      addParty(this.vote_table)
    },
    addConstituency: function () {
      addConstituency(this.vote_table)
    },
    pruneSmallParties: function () {
      const result = pruneSmallParties(this.vote_table, this.prune_percent)
      if (result.error) this.serverError(result.error)
      if (result.changed) {
        this.updateVoteSums()
        this.addBeforeunload()
      }
    },
    clearAll: function () {
      clearVoteTable(this.vote_table)
      this.show_party_names = false
      this.show_max_adj_seats = false
      this.updateVoteSums()
    },
    deletePartyVotes: function () {
      this.vote_table.party_vote_info.specified = false
      this.vote_table.party_vote_basis = "totals"
    },
    addPartyVotes: function() {
      let n = this.vote_table.parties.length
      this.vote_table.party_vote_info = {
        name: "–",
        num_fixed_seats: 0,
        num_adj_seats: 1,
        votes: Array(n).fill(1),
        specified: true,
        total: n,
        pruned: 0,
      }
    },
    addMaximumAdjustmentSeats: function () {
      addAdjustmentSeatMaximums(this.vote_table)
      this.show_max_adj_seats = true
    },
    removeMaximumAdjustmentSeats: function () {
      removeAdjustmentSeatMaximums(this.vote_table)
      this.show_max_adj_seats = false
    },
    addPartyNames: function() {
      this.$set(
        this.vote_table,
        "party_names",
        Array(this.vote_table.parties.length).fill("")
      )
      this.show_party_names = true
    },
    save: function () {
      var filename = this.vote_table.name.replace('þ', 'th')
      var table = {...this.vote_table, name: filename}
      let promise = axios({
        method: "post",
        url: "api/votes/save/",
        data: { vote_table: table },
        responseType: "arraybuffer",
      });
      this.downloadFile(promise)
    },
    loadPreset: function (_, election_id) {
      this.$refs.modalpresetref.hide();
      this.setWaitingForData()
      this.$http.post("api/presets/load/", {election_id: election_id }).then(
        (response) => {
          if (!response.body || response.body.error) {
            this.serverError(response.body) 
          } else {
            this.updateVoteTable(response.data)
            this.show_party_names = false
          }
          this.clearWaitingForData()
        },
        (response) => {
          this.serverError(response.status)
          this.clearWaitingForData()
        }
      )
    },
    loadVotes: function() {
      this.setWaitingForData()
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.$http.post("api/votes/upload/", formData).then(
        (response) => {
          if (!response.body || response.body.error) {
            this.serverError(response.body) 
          } else {
            this.updateVoteTable(response.data)
            this.show_party_names = false
          }
          this.clearWaitingForData()
        },
        (response) => {
          this.serverError(response.status)
          this.clearWaitingForData()
        }
      )
    },
    loadAll: function() {
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.uploadAll(formData)
    },
    checkVoteSeats: function() {
      return validConstituencySeats(this.vote_table)
    },
    checkVoteInput: function() {
      return validVotes(this.vote_table)
    },
    checkVoteLabels: function() {
      return validVoteTableLabels(this.vote_table)
    },
    checkPartyInput: function() {
      return validNationalVotes(this.vote_table)
    }
},
  watch: {
    vote_table: {
      handler: function () {
        this.show_max_adj_seats = Object.prototype.hasOwnProperty.call(
          this.vote_table, "max_total_adj_seats"
        )
        if (!this.waiting_for_data) {
          this.addBeforeunload()
          this.updateVoteSums()
        }
      },
      deep: true
    },
  }
};
</script>
