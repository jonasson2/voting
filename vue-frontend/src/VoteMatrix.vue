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
    <b-img rounded fluid src="/static/img/parties_xlsx.png" />
    <p>
      Optionally, if the second and third columns are named 'cons' or 'adj',
      they will be understood to be information about the number of
      constituency seats and adjustment seats, respectively, in each
      constituency. If you leave them out, you can specify the number of seats
      manually.
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
      The file provided should be a JSON file formatted lika a file
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
        title="Use preset votes and seat numbers from real or fictional elections"
        v-b-modal.modalpreset
        >
        Use preset
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Upload votes and seat numbers from local Excel or CSV file"
        v-b-modal.modalupload
        >
        Load from file
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1 mb-10">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Delete all votes and seat numbers"
        @click="clearAll()"
        >
        Delete
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download votes and seat numbers to local Excel xlsx-file."
        @click="save()"
        >
        Save
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
        Load all
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
        Save all
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <br />
  <h6> These source votes and seats are used as basis for allocation in the Single
    election tab and as expected values in the Simulated elections tab
  </h6>
  <table class="votematrix">
    <tr>
      <th class="tablename">
        <input
          type="text"
          v-autowidth="{ maxWidth: '320px', minWidth: '50px' }"
          v-model="vote_table.name"
          />
      </th>
      <th
        class="seatnumberheading"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Constituency seats"
        >
        # Cons.
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
          v-autowidth="{ maxWidth: '300px', minWidth: '60px' }"
          v-model="vote_table.parties[partyidx]"
          />
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
    <tr v-for="(constituency, conidx) in vote_table.constituencies">
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
          v-autowidth="{ maxWidth: '400px', minWidth: '135px' }"
          v-model="constituency['name']"
          />
      </th>
      <td class="numerical">
        <input
          type="text"
          style="text-align: right"
          v-autowidth="{ maxWidth: '200px', minWidth: '65px' }"
          v-model.number="constituency['num_const_seats']"
          />
      </td>
      <td class="numerical">
        <input
          type="text"
          v-autowidth="{ maxWidth: '200px', minWidth: '50px' }"
          v-model.number="constituency['num_adj_seats']"
          />
      </td>
      <td v-for="(party, partyidx) in vote_table.parties" class="numerical">
        <input
          type="text"
          v-autowidth="{ maxWidth: '300px', minWidth: '120px' }"
          v-model.number="vote_table.votes[conidx][partyidx]"
          />
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
      <td class="displayright">
        {{ vote_sums.tot }}
      </td>
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
  </table>
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
    ]),
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
    this.$http.get("/api/presets").then(
      (response) => {
        if (!response.body || response.body.error) {
          this.serverError(response.body) 
        } else {
          this.presets = response.body;
          this.updateVoteSums()
        }
      }
    )
    console.log("Created VoteMatrix");
  },
  methods: {
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
      this.vote_table.parties.splice(index, 1);
      for (let con in this.vote_table.votes) {
        this.vote_table.votes[con].splice(index, 1);
      }
    },
    deleteConstituency: function (index) {
      this.vote_table.constituencies.splice(index, 1);
      this.vote_table.votes.splice(index, 1);
    },
    addParty: function () {
      this.vote_table.parties.push("");
      for (let con in this.vote_table.votes) {
        this.vote_table.votes[con].push(1);
      }
    },
    addConstituency: function () {
      this.vote_table.constituencies.push({
        name: "-",
        num_const_seats: 1,
        num_adj_seats: 1,
      });
      this.vote_table.votes.push(
        Array(this.vote_table.parties.length).fill(1));
    },
    clearVotes: function () {
      let v = [];
      for (let con in this.vote_table.votes) {
        v = Array(this.vote_table.votes[con].length).fill(0);
        this.$set(this.vote_table.votes, con, v)
      }
    },
    clearAll: function () {
      this.vote_table.name = ""
      this.vote_table.constituencies = []
      this.vote_table.parties = []
      this.vote_table.votes = []
      this.updateVoteSums()
    },
    save: function () {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/votes/save",
        data: { vote_table: this.vote_table },
        responseType: "arraybuffer",
      });
      this.downloadFile(promise)
    },
    loadPreset: function (_, election_id) {
      this.$refs.modalpresetref.hide();
      this.setWaitingForData()
      console.log('election_id', election_id)
      this.$http.post("/api/presets/load/", {election_id: election_id }).then(
        (response) => {
          if (!response.body || response.body.error) {
            this.serverError(response.body) 
          } else {
            this.updateVoteTable(response.data)
            this.clearWaitingForData()
          }
        })
    },
    loadVotes: function() {
      this.setWaitingForData()
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.$http.post("/api/votes/upload/", formData).then(
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
    }
  },
  watch: {
    vote_table: {
      handler: function() {
        if (!this.waiting_for_data) {
          console.log("watching vote_table")
          this.addBeforeunload()
          this.updateVoteSums()
        }
      },
      deep: true
    }
  },
};
</script>
