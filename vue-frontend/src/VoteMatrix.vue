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
            v-model="matrix.name"
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
        <th v-for="(party, partyidx) in matrix.parties" class="partyname">
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
            v-model="matrix.parties[partyidx]"
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
      <tr v-for="(constituency, conidx) in matrix.constituencies">
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
        <td v-for="(party, partyidx) in matrix.parties" class="partyvotes">
          <input
            type="text"
            v-autowidth="{ maxWidth: '300px', minWidth: '75px' }"
            v-model.number="matrix.votes[conidx][partyidx]"
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
        <td v-for="(party, partyidx) in matrix.parties" class="displayright">
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
import VueInputAutowidth from "vue-input-autowidth";
Vue.use(VueInputAutowidth);

export default {
  props: {
    vote_sums: { default: {} },
    waitingForData: false
  },
  data: function () {
    return {
      matrix: {
        name: "Example values",
        parties: ["A", "B"],
        votes: [
          [1500, 2000],
          [2500, 1700],
        ],
        constituencies: [
          { name: "I", num_const_seats: 10, num_adj_seats: 2 },
          { name: "II", num_const_seats: 10, num_adj_seats: 3 },
        ],
      },
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
    this.$emit("set-waiting", true)
    this.$http.get("/api/presets").then(
      (response) => {
        this.presets = response.body;
      },
      (response) => {
        console.log("Error, response.body", response.body)
      }
    );
    this.$emit("set-waiting", false)
    this.$emit("update-vote-table", this.matrix, false);
    console.log("Created VoteMatrix");
  },
  watch: {
    matrix: {
      handler: function (val, oldVal) {
        this.$emit("update-vote-table", val);
      },
      deep: true,
    },
  },
  methods: {
    deleteParty: function (index) {
      this.matrix.parties.splice(index, 1);
      for (let con in this.matrix.votes) {
        this.matrix.votes[con].splice(index, 1);
      }
    },
    deleteConstituency: function (index) {
      this.matrix.constituencies.splice(index, 1);
      this.matrix.votes.splice(index, 1);
    },
    addParty: function () {
      this.matrix.parties.push("");
      for (let con in this.matrix.votes) {
        this.matrix.votes[con].push(1);
      }
    },
    addConstituency: function () {
      this.matrix.constituencies.push({
        name: "-",
        num_const_seats: 1,
        num_adj_seats: 1,
      });
      this.matrix.votes.push(Array(this.matrix.parties.length).fill(1));
    },
    clearVotes: function () {
      let v = [];
      for (let con in this.matrix.votes) {
        v = Array(this.matrix.votes[con].length).fill(0);
        this.$set(this.matrix.votes, con, v);
      }
    },
    clearAll: function () {
      this.matrix.name = "";
      this.matrix.constituencies = [];
      this.matrix.parties = [];
      this.matrix.votes = [];
    },
    save: function () {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/votes/save",
        data: { vote_table: this.matrix },
        responseType: "arraybuffer",
      });      
      this.$emit("download-file", promise);
    },
    loadPreset: function (eid) {
      this.$emit("set-waiting", true)
      this.$http.post("/api/presets/load/", { eid: eid }).then(
        (response) => {
          this.matrix = response.data;
        },
        (response) => {
          this.$emit("server-error", "Illegal format of presets file")
        }
      )
      this.$emit("set-waiting", false)
    },
    uploadVotes: function (evt) {
      if (!this.uploadfile) {
        evt.preventDefault();
      }
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.$emit("set-waiting", true)
      this.$http.post("/api/votes/upload/", formData).then(
        (response) => {
          this.matrix = response.data;
        },
        (response) => {
          this.$emit("server-error", "Cannot upload votes from this file")
        }
      )
      this.$emit("set-waiting", false)
    },
    pasteCSV: function (evt) {
      if (!this.paste.csv) {
        evt.preventDefault();
        return;
      }
      this.$http.post("/api/votes/paste/", this.paste).then(
        (response) => {
          this.matrix = response.data;
        },
        (response) => {
          console.log("Error:", response);
          // Error?
        }
      );
    },
  },
};
</script>
