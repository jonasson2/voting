<template>
<b-container fluid class="votematrix-container">
  <b-modal
    size="lg"
    id="modalupload"
    title="Upload CSV or XLSX file"
    @ok="uploadVotes"
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
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      ></b-form-file>
  </b-modal>
  
  <b-modal size="lg" id="modalpaste" title="Paste CSV" @ok="pasteCSV">
    <p>
      Here you can paste in comma separated values to override the current
      vote table.
    </p>
    <b-form-textarea
      id="id_paste_csv"
      v-model="paste.csv"
      placeholder="Add your vote data"
      rows="7"
      >
    </b-form-textarea>
    <b-form-checkbox
      v-model="paste.has_name"
      value="true"
      unchecked-value="false"
      >
      First row begins with name by which to refer to this vote table.
    </b-form-checkbox>
    <b-form-checkbox
      v-model="paste.has_parties"
      value="true"
      unchecked-value="false"
      >
      First row is a header with party names.
    </b-form-checkbox>
    <b-form-checkbox
      v-model="paste.has_constituencies"
      value="true"
      unchecked-value="false"
      >
      First column contains constituency names.
    </b-form-checkbox>
    <b-form-checkbox
      v-model="paste.has_constituency_seats"
      value="true"
      unchecked-value="false"
      >
      Second column contains constituency seats.
    </b-form-checkbox>
    <b-form-checkbox
      v-model="paste.has_constituency_adjustment_seats"
      value="true"
      unchecked-value="false"
      >
      Third column contains adjustment seats.
    </b-form-checkbox>
  </b-modal>
  
  <b-modal
    size="xl"
    id="modalpreset"
    ref="modalpresetref"
    title="Load preset"
    cancel-only
    >
    <b-table hover :items="presets" :fields="presetfields">
      <template v-slot:cell(actions)="row">
        <b-button
          size="sm"
          @click.stop="
                       loadPreset(row.item.id);
                       $refs.modalpresetref.hide();
                       "
          class="mr-1 mt-0 mb-0"
          >
          Load
        </b-button>
      </template>
    </b-table>
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
        title="Delete all vote and seat numbers"
        @click="clearAll()"
        >
        Delete
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download votes and seat numbers to local Excel xlsx-file. 
               You may need to change browser settings; see Help for details"
        @click="save()"
        >
        Save
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <br />
  <h6>
    These seats and votes are used as basis for allocation in the Single
    election tab and as expected values in the Simulated elections tab
  </h6>
  <table class="votematrix">
    <tr>
      <th class="tablename">
        <input
          type="text"
          v-autowidth="{ maxWidth: '400px', minWidth: '50px' }"
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
      <td class="partyseats">
        <input
          type="text"
          v-autowidth="{ maxWidth: '200px', minWidth: '60px' }"
          v-model.number="constituency['num_const_seats']"
          />
      </td>
      <td class="partyseats">
        <input
          type="text"
          v-autowidth="{ maxWidth: '200px', minWidth: '50px' }"
          v-model.number="constituency['num_adj_seats']"
          />
      </td>
      <td v-for="(party, partyidx) in vote_table.parties" class="partyvotes">
        <input
          type="text"
          v-autowidth="{ maxWidth: '300px', minWidth: '75px' }"
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
import { mapState } from 'vuex';
import VueInputAutowidth from "vue-input-autowidth";
Vue.use(VueInputAutowidth);

export default {
  computed: {
    ...mapState([
      'vote_table',
      'vote_sums',
      'waiting_for_data'
    ]),
  },
  data: function () {
    return {
      presets: [],
      presetfields: [
        { key: "name", sortable: true },
        { key: "year", sortable: true },
        { key: "country", sortable: true },
        { key: "actions" },
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
    this.$store.commit('waiting')
    this.$http.get("/api/presets").then(
      (response) => {
        this.presets = response.body;
        this.$store.commit("updateVoteSums")    
      },
      (response) => {
        console.log("Error, response.body", response.body)
      }
    );
    this.$store.commit('notWaiting')
    console.log("Created VoteMatrix");
  },
  watch: {
    vote_table: {
      handler: function(val, oldval) {
        console.log("watching vote_table")
        this.$store.commit("updateVoteSums")
        this.$store.dispatch("recalc_sys_const")
      },
      deep: true,
    },
  },
  methods: {
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
        this.$set(this.vote_table.votes, con, v);
      }
    },
    clearAll: function () {
      this.vote_table.name = "";
      this.vote_table.constituencies = [];
      this.vote_table.parties = [];
      this.vote_table.votes = [];
    },
    save: function () {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/votes/save",
        data: { vote_table: this.vote_table },
        responseType: "arraybuffer",
      });
      this.$emit("download-file", promise);
    },
    loadPreset: function (eid) {
      this.$store.commit('waiting')
      this.$http.post("/api/presets/load/", { eid: eid }).then(
        (response) => {
          this.$store.commit("updateVoteTable", response.data)
          this.$store.dispatch("recalc_sys_const")
        },
        (response) => {
          this.$store.commit("serverError", "Illegal format of presets file")
        },
        this.$store.commit('notWaiting')
      )
    },
    uploadVotes: function (evt) {
      this.$store.commit('waiting')
      if (!this.uploadfile) {
        evt.preventDefault();
      }
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.$http.post("/api/votes/upload/", formData).then(
        (response) => {
          this.$store.commit("updateVoteTable", response.data)
          this.$store.dispatch("recalc_sys_const")
        },
        (response) => {
          this.$store.commit("serverError", "Cannot upload votes from this file")
        },
        this.$store.commit('notWaiting')
      )
    },
    pasteCSV: function (evt) {
      this.$store.commit("waiting")
      if (!this.paste.csv) {
        evt.preventDefault();
        return;
      }
      this.$http.post("/api/votes/paste/", this.paste).then(
        (response) => {
          this.$store.commit("updateVoteTable", response.data)
          this.$store.dispatch("recalc_sys_const")
        },
        (response) => {
          console.log("Error:", response);
          // Error?
        },
        this.$store.commit("notWaiting")
      );
    },
  },
};
</script>
