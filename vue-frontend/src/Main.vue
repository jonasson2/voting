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
    <b-tab title="Single election" @click="calculate">
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
      this.$set(this.election_rules, idx, rules);
      // (this works too: this.election_rules.splice(idx, 1, rules))
    },
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    updateVoteTable: function(table) {
      this.vote_table = table;
    },
  }  
}
</script>
