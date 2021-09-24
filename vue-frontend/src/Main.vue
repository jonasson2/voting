<template>
<div>
  <b-navbar toggleable="md" type="dark" variant="info">
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <!-- <b-alert :show="server.waitingForData">Loading...</b-alert> -->
  <b-alert
    :show="server.error"
    dismissible
    @dismissed="server.error=false"
    variant="danger"
    >
    Server error. Try again in a few seconds...
  </b-alert>
  <!-- TODO: Sýna þess villu, en ekki bara blikka með henni. -->
  <!-- Auk þess kemur villa ("constituencies") sem á ekki að koma. -->
  <!-- <b-alert -->
  <!--   :show="server.errormsg != ''" -->
  <!--   dismissible -->
  <!--   @dismissed="server.errormsg=''" -->
  <!--   variant="danger" -->
  <!--   > -->
    <!--   Server error. {{server.errormsg}} -->
    <!-- </b-alert> -->
  <b-tabs
    active-nav-item-class="font-weight-bold"
    card
    >
    <b-tab title="Votes and seats" active>
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        :vote_sums="vote_sums"
        @save-votes="saveVotes"
        @update-vote-table="updateVoteTable"
        @server-error="serverError">
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems
        :server="server"
        :election_rules="election_rules"
        :simulation_rules="simulation_rules"
        @update-main-election-rules="updateMainElectionRules">
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->
      <Election
        ref="ElectionRef"
        :server="server"
        :vote_table="vote_table"
        :election_rules="election_rules"
        :activeTabIndex="activeTabIndex"
        @update-rules="updateMainElectionRules">
      </Election>
    </b-tab>
    <b-tab title="Simulated elections">
      <!-- <p>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate
        :server="server"
        :vote_table="vote_table"
        :election_rules="election_rules"
        :simulation_rules="simulation_rules"
        @update-rules="updateSimulationRules">
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
import VoteMatrix from './components/VoteMatrix.vue'
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
      server: {
        waitingForData: false,
        errormsg: '',
        error: false,
      },
      vote_table: {
        name: "",
        parties: [],
        constituencies: [],
        votes: [],
      },
      vote_sums: {
        cseats: 0,
        aseats: 0,
        row: [],
        col: [],
        tot: 0,
      },
      // election_rules contains several rules; see ElectionSettings.vue
      // and electionRules.py for the member variables of a rule
      election_rules: [{}],
      activeTabIndex: 0,
      uploadfile: null,
      simulation_rules: {
        simulation_count: 0,
        gen_method: "",
        distribution_parameter: 0,
      },
    }
  },
  
  methods: {
    serverError: function(error) {
      this.server.errormsg = error;
    },
    updateMainElectionRules: function(rules, idx) {
      this.$set(this.election_rules, idx, rules);
      // (this works too: this.election_rules.splice(idx, 1, rules))
    },
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    updateVoteTable: function(table) {
      this.vote_table = table;
      this.vote_sums.row = table.votes.map(y => y.reduce((a, b) => a+b));
      this.vote_sums.col = table.votes.reduce((a, b) => a.map((v,i) => v+b[i]));
      this.vote_sums.tot = this.vote_sums.row.reduce((a, b) => a + b, 0);
      this.vote_sums.cseats = 0;
      this.vote_sums.aseats = 0;
      var c = table.constituencies;
      for (var i=0; i<c.length; i++) {
        this.vote_sums.cseats += c[i].num_const_seats;
        this.vote_sums.aseats += c[i].num_adj_seats;
      }
    },
    saveVotes: function (matrix, url) {
      // Thanks to Pétur Helgi Einarsson for this function
      let use_axios = true;
      
      let myPromise;
      if (use_axios) {
        myPromise = axios({
          method: "post",
          url: url,
          data: { vote_table: matrix },
          responseType: "arraybuffer",
        });
      } else {
        myPromise = this.$http.post(
          url,
          { vote_table: matrix },
          {
            responseType: "arraybuffer",
          }
        );
      }
      
      myPromise
        .then((response) => {
          if (use_axios) {
            return response;
          }
          
          let headers = {};
          for (let key in response.headers.map) {
            let val = response.headers.map[key];
            if (Array.isArray(val) && val.length == 1) {
              headers[key] = val[0];
            } else {
              headers[key] = val;
            }
          }
          response.headers = headers;
          
          let old_key = "body";
          let new_key = "data";
          
          Object.defineProperty(
            response,
            new_key,
            Object.getOwnPropertyDescriptor(response, old_key)
          );
          delete response[old_key];
          
          return response;
        })
        .then(
          (response) => {
            const status = response.status;
            console.log("response: ", response);
            
            if (status != 200) {
              this.$emit("server-error", response.body.error);
            } else {
              let link = document.createElement("a");
              var content_type = response.headers["content-type"];
              
              // Get filename from headers.
              const content_disposition =
                    response.headers["content-disposition"];
              let parts = content_disposition.split(";");
              let download_name = "Example";
              for (var i_part in parts) {
                let part = parts[i_part];
                let filename_pos = part.indexOf("filename=");
                if (filename_pos != -1) {
                  filename_pos += "filename=".length;
                  download_name = part.substring(filename_pos);
                }
              }
              
              var blob = new Blob([response.data], {
                type: content_type,
              });
              
              const blobUrl = URL.createObjectURL(blob);
              link.href = blobUrl;
              link.download = download_name;
              document.body.appendChild(link);
              
              // Dispatch click event on the link (this is necessary
              // as link.click() does not work on the latest Firefox
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
  }
}
</script>
