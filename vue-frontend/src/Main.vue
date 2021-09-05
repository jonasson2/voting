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
      style="margin-top:10px"
      active-nav-item-class="font-weight-bold"
      >
    <b-tab title="Votes and seats" active>
      <!-- <p>Specify reference votes and seat numbers</p> -->
        <VoteMatrix
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
          @update-main-election-rules="updateMainElectionRules">
        </ElectoralSystems>
      </b-tab>
    <b-tab title="Single election" @click="recalculate">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->
        <Election
          ref="ElectionRef"
          :server="server"
          :vote_table="vote_table"
          :results="results"
          :election_rules="election_rules"
          :activeTabIndex="activeTabIndex"
          @update-rules="updateMainElectionRules">
        </Election>
      </b-tab>
    <b-tab title="Simulate elections">
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
        name: "My reference votes",
        parties: ["A", "B"],
        votes: [[1500, 2000],
                [2500, 1700]],
        constituencies: [
          {"name": "I",  "num_const_seats": 10, "num_adj_seats": 2},
          {"name": "II", "num_const_seats": 10, "num_adj_seats": 3}
        ],
      },
      results: [],
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
  watch: {
    'vote_table': {
      handler: function (val, oldVal) {
        console.log("watching vote_table");
        this.recalculate();
      },
      deep: true
    },
    'election_rules': {
      handler: function (val, oldVal) {
        console.log("watching election_rules");
        this.recalculate();
      },
      deep: true
    },
  },
  
  methods: {
    serverError: function(error) {
      this.server.errormsg = error;
    },
    updateVoteMatrix: function(matrix) {
      console.log("updating matrix");
      console.log(matrix);
      this.VoteMatrix = matrix;
    },
    updateMainElectionRules: function(rules, idx) {
      this.$set(this.election_rules, idx, rules);
      // (this works too: this.election_rules.splice(idx, 1, rules))
    },
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    recalculate: function() {
      console.log("recalculate called");
      if (this.election_rules.length > 0) {
        this.server.waitingForData = true;
        this.$http.post('/api/election/',
                        {
                          vote_table: this.vote_table,
                          rules: this.election_rules,
                        }).then(response => {
                          if (response.body.error) {
                            this.server.errormsg = response.body.error;
                            this.server.waitingForData = false;
                          } else {
                            this.server.errormsg = '';
                            this.server.error = false;
                            this.results = response.body;
                            for (var i=0; i<response.body.length; i++){
                              let old_const = this.election_rules[i].constituencies;
                              let new_const = response.body[i].rules.constituencies;
                              let modified = false;
                              if (new_const.length == old_const.length) {
                                for (var j=0; j<new_const.length; j++) {
                                  let old_c = old_const[j];
                                  let new_c = new_const[j];
                                  if (old_c.name != new_c.name
                                      || old_c.num_const_seats != new_c.num_const_seats
                                      || old_c.num_adj_seats != new_c.num_adj_seats) {
                                    modified = true;
                                  }
                                }
              }
              else if (new_const.length>0) {
                modified = true;
              }
              if (modified){
                this.$set(this.election_rules, i, response.body[i].rules);
              }
            }
            this.server.waitingForData = false;
          }
        }, response => {
          this.server.error = true;
          this.server.waitingForData = false;
        });
      }
    },
  }  
}
</script>
