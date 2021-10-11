<template>
<div>
  <b-navbar toggleable="md" type="dark" variant="info">
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <!-- <b-alert :show="server.waitingForData">Loading...</b-alert> -->
  <!-- <b-alert -->
  <!--   :show="server.error" -->
  <!--   dismissible -->
  <!--   @dismissed="server.error=false" -->
  <!--   variant="danger" -->
  <!--   > -->
  <!--   Server error. Try again in a few seconds... -->
  <!-- </b-alert> -->
  <!-- TODO: Sýna þess villu, en ekki bara blikka með henni. -->
  <!-- Auk þess kemur villa ("constituencies") sem á ekki að koma. -->
  <b-alert
    :show="server.errormsg != ''"
    dismissible
    @dismissed="server.errormsg=''"
    variant="danger"
    >
    Server error. {{server.errormsg}}
  </b-alert>
  <b-tabs
    active-nav-item-class="font-weight-bold"
    card
    >
    <b-tab title="Votes and seats" active>
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        :vote_sums="vote_sums"
        @server-error="serverError"
        @download-file="downloadFile"
        @update-vote-table="updateVoteTable">
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems
        :main_rules="rules"
        :constituencies="constituencies"
        @server-error="serverError"
        @update-main-election-rules="updateMainElectionRules"
        @update-main-simulation-rules="updateSimulationRules"
        @download-file="downloadFile"
        @save-settings="saveSettings">
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election" @click="recalculate()">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->
      <Election
        ref="ElectionRef"
        :vote_table="vote_table"
        :main_election_rules="rules.election_rules"
        :results="results"
        @server-error="serverError"
        @download-file="downloadFile"
        @update-rules="updateMainElectionRules">
      </Election>
    </b-tab>
    <b-tab title="Simulated elections">
      <!-- <p>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate
        :server="server"
        :main_rules="rules"
        :vote_table="vote_table"
        @server-error="serverError"
        @update-main-rules="updateSimulationRules"
        @download-file="downloadFile">
      </Simulate>
    </b-tab>
    <b-tab title="Help">
      <Intro>
      </Intro>
    </b-tab>
  </b-tabs>
  </b-card>
</div>
</template>

<script>
import Election from './Election.vue'
import ElectoralSystems from './ElectoralSystems.vue'
import Simulate from './Simulate.vue'
import VoteMatrix from './VoteMatrix.vue'
import Intro from './Intro.vue'

export default {
  components: {
    VoteMatrix,
    Election,
    Simulate,
    ElectoralSystems,
    Intro,
  },
  
  data: function() {
    return {
      constituencies: [],
      server: {
        waitingForData: false,
        errormsg: '',
        error: false,
      },
      vote_table: {},
      vote_sums: {
        cseats: 0,
        aseats: 0,
        row: [],
        col: [],
        tot: 0,
      },
      // election_rules contains several rules; see ElectionSettings.vue
      // and electionRules.py for the member variables of a rule
      rules: {
        election_rules: [{}],
        simul_settings: {}
      },
      activeTabIndex: 0,
      uploadfile: null,
      results: {},
      // simul_settings: {
      //   simulation_count: 0,
      //   gen_method: "",
      //   distribution_parameter: 0,
      // },
    }
  },
  
  methods: {
    serverError: function(error) {
      this.server.errormsg = error;
    },
    updateMainElectionRules: function(rules) {
      this.rules.election_rules = rules
      //this.recalculate();
    },
    updateSimulationRules: function(rules) {
      console.log("updateSimulationRules in Main")
      this.rules.simul_settings = rules;
      console.log("this.rules.simul_settings=", this.rules.simul_settings)
    },
    updateVoteTable: function(table) {
      console.log("Updating vote table")
      this.vote_table = table
      this.vote_sums.row = table.votes.map(y => y.reduce((a, b) => a+b))
      this.vote_sums.col = table.votes.reduce((a, b) => a.map((v,i) => v+b[i]))
      this.vote_sums.tot = this.vote_sums.row.reduce((a, b) => a + b, 0)
      this.vote_sums.cseats = 0
      this.vote_sums.aseats = 0
      var c = table.constituencies
      for (var i=0; i<c.length; i++) {
        this.vote_sums.cseats += c[i].num_const_seats
        this.vote_sums.aseats += c[i].num_adj_seats
      }
      this.constituencies = c;
    },
    // Thanks to Pétur Helgi Einarsson for the next two functions
    parse_headers: function (headers) {
      // Return type and name for download file
      var content_type = headers["content-type"];
      var content_disposition = headers["content-disposition"];
      let parts = content_disposition.split(";");
      let download_name = "Example.xlsx"
      for (var i_part in parts) {
        let part = parts[i_part];
        let filename_pos = part.indexOf("filename=");
        if (filename_pos != -1) {
          filename_pos += "filename=".length;
          download_name = part.substring(filename_pos);
        }
      }
      return [content_type, download_name]
    },
    saveSettings: function() {
      let promise = axios({
        method: "post",
        url: "/api/settings/save",
        data: {
          e_settings: this.rules.election_rules,
          sim_settings: this.rules.simul_settings
        },
        responseType: "arraybuffer",
      });
      this.downloadFile(promise);
    },
    downloadFile: function (promise) {
      promise
        .then(
          (response) => {
            const status = response.status;
            if (status != 200) {
              this.$emit("server-error", response.body.error);
            } else {
              let link = document.createElement("a");
              const [type, downloadname] = this.parse_headers(response.headers);
              const blob = new Blob([response.data], {type: type});
              const blobUrl = URL.createObjectURL(blob);
              link.href = blobUrl;
              link.download = downloadname;
              document.body.appendChild(link);
              // Dispatch click event on the link (this is necessary
              // as link.click() does not work in the latest Firefox
              link.dispatchEvent(
                new MouseEvent("click", {
                  bubbles: true,
                  cancelable: true,
                  view: window,
                })
              );
              link.remove();
            }
          },
          (response) => {
            console.log("Error:", response);
          }
        );
    },
    recalculate: function() {
      console.log("Election recalculate called");
      if (this.rules.election_rules.length > 0) {
        // && this.election_rules.length > this.activeTabIndex
        // && this.election_rules[this.activeTabIndex].name) {
        this.server.waitingForData = true;
        this.$http.post(
          '/api/election/',
          {
            vote_table: this.vote_table,
            rules: this.rules.election_rules,
          }).then(response => {
            if (response.body.error) {
              console.log("error-return 1")
              this.server.errormsg = response.body.error;
              this.server.waitingForData = false;
            } else {
              this.server.errormsg = '';
              this.server.error = false;
              this.results = response.body;
              console.log("results", this.results);
              for (var i=0; i<response.body.length; i++){
                // let old_const = this.election_rules[i].constituencies;
                // let new_const = response.body[i].rules.constituencies;
                // let modified = false;
                // if (new_const.length == old_const.length) {
                //   for (var j=0; j<new_const.length; j++) {
                //     let old_c = old_const[j];
                //     let new_c = new_const[j];
                //     if (old_c.name != new_c.name
                //         || old_c.num_const_seats != new_c.num_const_seats
                //         || old_c.num_adj_seats != new_c.num_adj_seats) {
                //       modified = true;
                //     }
                //   }
                // }
                // else if (new_const.length>0) {
                //   modified = true;
                // }
                // if (modified){
                //   this.$emit('update-rules', response.body[i].rules, i);
                // }
                //this.updateMainElectionRules(response.body[i].rules, i);
              }
              this.server.waitingForData = false;
            }
          }, response => {
            console.log("error-return 2")
            console.log("response", response.body)
            this.server.error = true;
            this.server.waitingForData = false;
          });
      }
    },
  }
}
</script>
