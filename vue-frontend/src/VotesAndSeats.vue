<template>
  <div>
    <h2>Votes</h2>
    <VoteMatrix
      @update-vote-table="updateVoteTable"
      @server-error="serverError">
    </VoteMatrix>

    <b-alert :show="server.waitingForData">Loading...</b-alert>
    <b-alert :show="server.error" dismissible @dismissed="server.error=false" variant="danger">Server error. Try again in a few seconds...</b-alert>
    <b-alert :show="server.errormsg != ''" dismissible @dismissed="server.errormsg=''" variant="danger">Server error. {{server.errormsg}}</b-alert>

    <b-tabs style="margin-top:10px">
      <b-tab title="Single Election" active>
        <Election
          :server="server"
          :vote_table="vote_table"
          :election_rules="election_rules"
          :activeTabIndex="activeTabIndex"
          @update-rules="updateElectionRules">
        </Election>
      </b-tab>
      <b-tab title="Simulation">
        <Simulate
          :server="server"
          :vote_table="vote_table"
          :election_rules="election_rules"
          :simulation_rules="simulation_rules"
          @update-rules="updateSimulationRules">
        </Simulate>
      </b-tab>
    </b-tabs>
  </div>
</template>

<script>
import Election from './Election.vue'
import Simulate from './Simulate.vue'
import VoteMatrix from './components/VoteMatrix.vue'
import ElectionSettings from './components/ElectionSettings.vue'

export default {
  components: {
    VoteMatrix,
    ElectionSettings,
    Election,
    Simulate,
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
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    updateVoteTable: function(table) {
      this.vote_table = table;
    },
  }
}
</script>
