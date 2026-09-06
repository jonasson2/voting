<template>
<b-container fluid class="votematrix-container">
  <b-modal
    size="lg"
    id="modalupload"
    ref="modaluploadref"
    title="Upload CSV or XLSX file"
    >
    <p>
      The file provided must be a CSV or an Excel XLSX file formatted with
      parties on the first row and constituency names on the first column.
    </p>
    <b-img rounded fluid src="static/img/parties_xlsx.png" />
    <p>
      Optionally, if the second and  third columns  are named 'fixed'  or 'adj',
      they will be understood to be  information about the number of fixed seats
      and adjustment seats, respectively, in each  constituency. If  you leave
      them out, you can specify the number of seats manually.
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
    <div class="table-scroll">
    <table class="votematrix">
      <tbody>
      <tr>
        <th class="topleft">
        </th>
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
          title="Adjustment seats"
          >
          # Adj.
        </th>
        <th v-for="(party, partyidx) in vote_table.parties" class="partyname">
          <b-button
            class="xbutton"
            style="padding: 0"
            size="sm"
            variant="link"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Remove Party"
            @click="deleteParty(partyidx)"
            >
            X
          </b-button>
          <input
            type="text"
            style="text-align: center"
            v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
            v-model="vote_table.parties[partyidx]"
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
            @click="addParty()"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Add party"
            >
            <b>+</b>
          </b-button>
        </th>
      </tr>
      <tr v-for="(constituency, conidx) in vote_table.constituencies" size="sm">
        <th class="constname">
          <b-button
            style="padding: 0"
            size="sm"
            variant="link"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Remove constituency"
            @click="deleteConstituency(conidx)"
            >
            X
          </b-button>
          <input
            type="text"
            v-autowidth="{ maxWidth: '400px', minWidth: '25px' }"
            v-model="constituency['name']"
            />
        </th>
        <td class="numerical" size="sm">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
            v-model.number="constituency['num_fixed_seats']"
            />
        </td>
        <td class="numerical" size="sm">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
            v-model.number="constituency['num_adj_seats']"
            />
        </td>
        <td v-for="(party, partyidx) in vote_table.parties" class="numerical">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
            v-model.number="vote_table.votes[conidx][partyidx]"
            />
        </td>
        <td v-if="hasPrunedVotes" class="displayright">
          {{ vote_table.pruned[conidx] }}
        </td>
        <td class="displayright">
          {{ vote_sums.row[conidx] }}
        </td>
      </tr>
      <tr>
        <th class="displayleft">Total</th>
        <td class="displayright">
          {{ vote_sums.cseats }}
        </td>
        <td class="displayright">
          {{ vote_sums.aseats }}
        </td>
        <td v-for="(party, partyidx) in vote_table.parties" class="displayright">
          {{ vote_sums.col[partyidx] }}
        </td>
        <td v-if="hasPrunedVotes" class="displayright">
          {{ vote_sums.pruned }}
        </td>
        <td class="displayright">
          {{ vote_sums.tot }}
        </td>
      </tr>
      <tr>
        <th class="displayleft">Vote share</th>
        <td></td>
        <td></td>
        <td v-for="(party, partyidx) in vote_table.parties" class="displayright">
          {{ votePercentage(vote_sums.col[partyidx]) }}
        </td>
        <td v-if="hasPrunedVotes" class="displayright">
          {{ votePercentage(vote_sums.pruned) }}
        </td>
        <td class="displayright">{{ votePercentage(vote_sums.tot) }}</td>
      </tr>
      <tr>
        <th class="growtable">
          <b-button
            size="sm"
            @click="addConstituency()"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Add constituency"
            >
            <b>+</b>
          </b-button>
        </th>
      </tr>
      </tbody>
    </table>
    </div>
  <b-alert :show="checkVoteSeats()==false">
    Some seats are not in numerical format
  </b-alert>
  <b-alert :show="checkVoteInput()==false">
    Some votes are not in numerical format
  </b-alert>
  
  
  <b-row>
    <b-col cols="auto">
    <legend style = "margin-left:0px; margin-top:12px"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title='Seat numbers and votes for the national list (German
                   "zveitstimmen", New Zealand "party votes").'
            >
      National party votes and seats
    </legend>
    </b-col>
  </b-row>
    <div class="table-scroll">
    <table class="votematrix">
      <tbody>
      <tr v-if="vote_table.party_vote_info.specified" size="sm">
        <th class="topleft">
        </th>
        <th
          class="seatnumberheading" 
          v-b-tooltip.hover.bottom.v-primary.ds500
          title='National fixed seats, allocated according to the national party votes
                 using the fixed seat allocation rules set in the "Electoral systems" tab. 
                 Normally there are no national fixed seats, but if specified then the 
                 national party votes must not be left blank.'
          >
          # Fixed
        </th>
        <th
          class="seatnumberheading"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="National adjustment seats. These are allocated last, by filling
                 each party's remaining seats after the allocation of all other 
                 seats (no votes are used for this allocation)"
          >
          # Adj.
        </th>
        <th v-for="(party, partyidx) in vote_table.parties" class="displaycenter">
          {{vote_table.parties[partyidx]}}
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
      <tr v-if="vote_table.party_vote_info.specified" size="sm">
        <th class="constname">
          <b-button
            style="padding: 0"
            size="sm"
            variant="link"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Remove party votes"
            @click="deletePartyVotes()"
            >
            X
          </b-button>
          <input
            type="text"
            v-autowidth="{ maxWidth: '400px', minWidth: '25px' }"
            v-model="vote_table.party_vote_info.name"
            />
        </th>
        <td class="numerical" size="sm">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
            v-model.number="vote_table.party_vote_info['num_fixed_seats']"
            />
        </td>
        <td class="numerical" size="sm">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '200px', minWidth: '25px' }"
            v-model.number="vote_table.party_vote_info['num_adj_seats']"
            />
        </td>
        <td v-for="(party, partyidx) in vote_table.parties" class="numerical">
          <input
            type="text"
            style="text-align: right"
            v-autowidth="{ maxWidth: '300px', minWidth: '25px' }"
            v-model.number="vote_table.party_vote_info.votes[partyidx]"
            />
        </td>
        <td v-if="hasPrunedVotes" class="displayright">
          {{ vote_table.party_vote_info.pruned }}
        </td>
        <td class="displayright">
          {{vote_table.party_vote_info.total}}
        </td>
      </tr>
      <tr v-if="!vote_table.party_vote_info.specified">
        <th class="growtable">
          <b-button
            size="sm"
            @click="addPartyVotes()"
            v-b-tooltip.hover.right.v-primary.ds500
            title="Add party votes"
            >
            <b>+</b>
          </b-button>
        </th>
      </tr>
      </tbody>
    </table>
    </div>
  <div
    v-if="vote_table.party_vote_info.specified"
    class="settings-row party-vote-basis-row"
    >
    <label class="settings-field">
      <span>Votes used as basis for party totals</span>
      <b-form-select class="compact-select settings-vote-basis"
        v-model="vote_table.party_vote_basis"
        :options="partyVoteBasisOptions"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="The total number of seats for each party is computed using the votes selected here."/>
    </label>
  </div>
  <b-alert :show="checkPartyInput()==false">
    National: Some seats or votes are not in numerical format
  </b-alert>
  
</b-container>
</template>

<script>
import Vue from "vue";
import { mapState,mapMutations,mapActions } from 'vuex';
import VueInputAutowidth from "vue-input-autowidth";
Vue.use(VueInputAutowidth);

export default {
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
      paste: {
        csv: "",
        has_name: false,
        has_parties: false,
        has_constituencies: false,
        has_constituency_seats: false,
        has_constituency_adjustment_seats: false,
      },
    };
  },
  created: function () {
    console.log("Creating VoteMatrix")
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
    console.log(Vue.version)
    console.log("Created VoteMatrix");
  },
  methods: {
    votePercentage(votes) {
      const total = this.vote_sums.tot;
      if (!Number.isFinite(votes) || !Number.isFinite(total) || total <= 0) return "–";
      return (100 * votes / total).toFixed(1) + "%";
    },
    ...mapMutations([
      "updateVoteSums",
      "updateVoteTable",
      "updateSystems",
      "updateSimSettings",
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
      this.vote_table.parties.splice(index, 1)
      for (let con in this.vote_table.votes) {
        this.vote_table.votes[con].splice(index, 1)
      }
      if (this.vote_table.party_vote_info.specified)
        this.vote_table.party_vote_info.votes.splice(index, 1)
    },
    deleteConstituency: function (index) {
      this.vote_table.constituencies.splice(index, 1);
      this.vote_table.votes.splice(index, 1)
      this.vote_table.pruned.splice(index, 1)
    },
    addParty: function () {
      this.vote_table.parties.push("");
      for (let con in this.vote_table.votes) {
        this.vote_table.votes[con].push(1);
      }
      if (this.vote_table.party_vote_info.specified)
        this.vote_table.party_vote_info.votes.push(1)
    },
    addConstituency: function () {
      this.vote_table.constituencies.push({
        name: "–",
        num_fixed_seats: 1,
        num_adj_seats: 1,
      });
      this.vote_table.votes.push(
        Array(this.vote_table.parties.length).fill(1));
      this.vote_table.pruned.push(0)
    },
    pruneSmallParties: function () {
      let threshold = Number(this.prune_percent)
      if (!Number.isFinite(threshold) || threshold < 0 || threshold > 100) {
        this.serverError("Small party cutoff must be a number from 0 to 100")
        return
      }
      if (this.vote_table.parties.length == 0 || this.vote_table.votes.length == 0) {
        return
      }
      let party_totals = this.vote_table.parties.map((_, partyidx) =>
        this.vote_table.votes.reduce((total, row) => total + row[partyidx], 0)
      )
      let total_votes = party_totals.reduce((a, b) => a + b, 0)
        + this.vote_table.pruned.reduce((a, b) => a + b, 0)
      if (total_votes <= 0) {
        return
      }
      let keep = party_totals.map(total => total/total_votes*100 >= threshold)
      if (!keep.some(Boolean)) {
        this.serverError("Small party cutoff would remove all parties")
        return
      }
      if (keep.every(Boolean)) {
        return
      }
      this.vote_table.pruned = this.vote_table.votes.map(
        (row, conidx) => this.vote_table.pruned[conidx]
          + row.reduce(
            (total, votes, partyidx) => total + (keep[partyidx] ? 0 : votes),
            0
          )
      )
      this.vote_table.parties = this.vote_table.parties.filter((_, partyidx) => keep[partyidx])
      this.vote_table.votes = this.vote_table.votes.map(row =>
        row.filter((_, partyidx) => keep[partyidx])
      )
      if (this.vote_table.party_vote_info.specified) {
        this.vote_table.party_vote_info.pruned +=
          this.vote_table.party_vote_info.votes.reduce(
            (total, votes, partyidx) => total + (keep[partyidx] ? 0 : votes),
            0
          )
        this.vote_table.party_vote_info.votes =
          this.vote_table.party_vote_info.votes.filter((_, partyidx) => keep[partyidx])
      }
      this.updateVoteSums()
      this.addBeforeunload()
    },
    clearAll: function () {
      this.vote_table.name = ""
      this.vote_table.constituencies = []
      this.vote_table.parties = []
      this.vote_table.votes = []
      this.vote_table.pruned = []
      this.vote_table.party_vote_info.specified = false
      this.vote_table.party_vote_info.pruned = 0
      this.vote_table.party_vote_basis = "totals"
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
      console.log('election_id', election_id)
      this.$http.post("api/presets/load/", {election_id: election_id }).then(
        (response) => {
          if (!response.body || response.body.error) {
            this.serverError(response.body) 
          } else {
            console.log("body=", response.body)
            console.log("data=", response.data)
            this.updateVoteTable(response.data)
            this.clearWaitingForData()
          }
        })
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
            this.clearWaitingForData()
          }
        })
    },
    loadAll: function() {
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.uploadAll(formData)
    },
    checkVoteSeats: function() {
      return this.vote_table.constituencies.map(({ num_fixed_seats }) => num_fixed_seats).every(function(element) {return typeof element == 'number';})
          && this.vote_table.constituencies.map(({ num_adj_seats }) => num_adj_seats).every(function(element) {return typeof element == 'number';})
    },
    checkVoteInput: function() {
      for (let element of this.vote_table.votes){
        let numbers = element.every(function(el) {return typeof el == 'number';})
        if (numbers == false){
          return numbers
        }
      }
      return true
    },
    checkPartyInput: function() {
      return this.vote_table.party_vote_info.votes.every(function(element) {return typeof element == 'number';})
          && typeof this.vote_table.party_vote_info.num_adj_seats == 'number'
          && typeof this.vote_table.party_vote_info.num_fixed_seats == 'number'
    }
},
  watch: {
    vote_table: {
      handler: function () {
        console.log('vote_table changed')
        console.log(this.vote_table.name)
        if (!this.waiting_for_data) {
          console.log("watching vote_table")
          this.addBeforeunload()
          this.updateVoteSums()
        }
      },
      deep: true
    },
  }
};
</script>
