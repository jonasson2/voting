<template>
  <div>
    <b-navbar toggleable="md" type="dark" variant="info">
      <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
      <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
    </b-navbar>
    <b-alert :show="server.waitingForData">Loading...</b-alert>
    <b-alert :show="server.error" dismissible @dismissed="server.error=false" variant="danger">Server error. Try again in a few seconds...</b-alert>
    <b-alert :show="server.errormsg != ''" dismissible @dismissed="server.errormsg=''" variant="danger">Server error. {{server.errormsg}}</b-alert>

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
        <p>Define one or several electoral systems by specifying apportionment rules and modifying seat numbers</p>
        <ElectoralSystems
          :server="server"
          :election_rules="election_rules"
        >
        </ElectoralSystems>
      </b-tab>
      <b-tab title="Single Election" @click:calculate()>
        <p>Calculate results for the reference votes and a selected electoral system</p>
        <Election
          :server="server"
          :vote_table="vote_table"
          :election_rules="election_rules"
          :activeTabIndex="activeTabIndex"
          @update-rules="updateElectionRules">
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
      needsToRefresh: false,
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
    calculate: function() {
      console.log("hi");
      this.needsToRefresh = true;
    },
    addElectionRules: function() {
      this.election_rules.push({})
    },
    deleteElectionRules: function(idx) {
      this.election_rules.splice(idx, 1);
    },
    updateElectionRules: function(rules, idx) {
      this.$set(this.election_rules, idx, rules);
      //this works too: this.election_rules.splice(idx, 1, rules);
    },
    updateElectionRulesAndActivate: function(rules, idx) {
      this.updateElectionRules(rules, idx);
      this.activeTabIndex = idx;
    },
    updateSimulationRules: function(rules) {
      this.simulation_rules = rules;
    },
    saveSettings: function() {
      this.$http.post('/api/settings/save/', {
        e_settings: this.election_rules,
        sim_settings: this.simulation_rules,
      }).then(response => {
        if (response.body.error) {
          this.server.errormsg = response.body.error;
          //this.$emit('server-error', response.body.error);
        } else {
          let link = document.createElement('a')
          link.href = '/api/downloads/get?id=' + response.data.download_id
          link.click()
        }
      }, response => {
        console.log("Error:", response);
      })
    },
    uploadSettingsAndAppend: function(evt) {
      var replace = false;
      this.uploadSettings(evt, replace);
      this.$refs['appendFromFile'].reset();
    },
    uploadSettingsAndReplace: function(evt) {
      var replace = true;
      this.uploadSettings(evt, replace);
      this.$refs['replaceFromFile'].reset();
    },
    uploadSettings: function(evt, replace) {
      if (!this.uploadfile) {
        evt.preventDefault();
      }
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.$http.post('/api/settings/upload/', formData).then(response => {
        if (replace){
          this.election_rules = [];
        }
        for (const setting of response.data.e_settings){
          this.election_rules.push(setting);
        }
        if (response.data.sim_settings){
          this.simulation_rules = response.data.sim_settings;
        }
      });
    },
    updateVoteTable: function(table) {
      this.vote_table = table;
    },
  }  
}
</script>
