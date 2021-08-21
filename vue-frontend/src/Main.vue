<template>
  <div>
    <b-navbar toggleable="md" type="dark" variant="info">
      <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
      <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
    </b-navbar>
    <b-alert :show="server.waitingForData">Loading...</b-alert>
  <b-alert
    :show="server.error"
    dismissible
    @dismissed="server.error=false"
    variant="danger"
    >
    Server error. Try again in a few seconds...
  </b-alert>
  <b-alert
    :show="server.errormsg != ''"
    dismissible
    @dismissed="server.errormsg=''"
    variant="danger"
    >
    Server error. {{server.errormsg}}
  </b-alert>
    <b-tabs
      style="margin-top:10px"
      active-nav-item-class="font-weight-bold"
      >
      <b-tab title="Votes and Seats" active>
        <p>Specify reference votes and seat numbers</p>
        <VoteMatrix
          @update-vote-table="updateVoteTable"
          @server-error="serverError">
        </VoteMatrix>
      </b-tab>
      <b-tab title="Electoral Systems">
      <p>Define one or several electoral systems by specifying apportionment
        rules and modifying seat numbers</p>
        <ElectoralSystems
          :server="server"
          :election_rules="election_rules"
          @update-main-election-rules="updateMainElectionRules">
        </ElectoralSystems>
      </b-tab>
      <b-tab title="Single Election" @click="calculate">
        <p>Calculate results for the reference votes and a selected electoral system</p>
        <Election
          ref="ElectionRef"
          :server="server"
          :vote_table="vote_table"
          :election_rules="election_rules"
          :activeTabIndex="activeTabIndex"
          @do-recalculate="mainrecalculate"
          @update-rules="updateMainElectionRules">
        </Election>
      </b-tab>
      <b-tab title="Simulation">
        <p>Simulate several elections and compute results for each specified electoral system</p>
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
        name: "",
        parties: [],
        constituencies: [],
        votes: [],
      },
      // election_rules contains several rules; see ElectionSettings.vue
      // and electionRules.py for the member variables of a rule
      election_rules: [{}],
      activeTabIndex: 0,
      uploadfile: null,
      results: [],
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
    calculate: function() {
      //this.$refs.ElectionRef.recalculate();
    },
    updateMainElectionRules: function(rules, idx) {
      var old = this.election_rules[0];
      console.log("Updated main election rules:");
      console.log("old name:", this.election_rules[0].name);
      if (old.constituencies != null && old.constituencies.length > 0)
        console.log(old.constituencies[0].name)
      console.log("new name:", rules.name);
      if (rules.constituencies != null && rules.constituencies.length > 0)
        console.log(rules.constituencies[0].name)
      this.$set(this.election_rules, idx, rules);
      // (this works too: this.election_rules.splice(idx, 1, rules))
    },
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    updateVoteTable: function(table) {
      this.vote_table = table;
    },

    mainrecalculate: function() {
      console.log("mainrecalculate called");
      if (this.election_rules.length > 0
          && this.election_rules.length > this.activeTabIndex
          && this.election_rules[this.activeTabIndex].name) {
        this.server.waitingForData = true;
        this.$http.post('/api/election/',
        {
          vote_table: this.vote_table,
          rules: this.election_rules,
        }).then(response => {
          if (response.body.error) {
            console.log("**************** ERROR-1 **************");
            this.server.errormsg = response.body.error;
            this.server.waitingForData = false;
          } else {
            console.log("**************** SUCCESS **************");
            this.server.errormsg = '';
            this.server.error = false;
            this.results = response.body;
            console.log("results", this.results);
            console.log("length", response.body.length);
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
              console.log("modified", modified);
              if (modified){
                this.updateMainElectionRules(response.body[i].rules, i);
                //this.$emit('update-rules', response.body[i].rules, i);
              }
            }
            this.server.waitingForData = false;
          }
        }, response => {
          console.log("**************** ERROR-2 **************");
          this.server.error = true;
          this.server.waitingForData = false;
        });
      }
    },
  }  
}
</script>
