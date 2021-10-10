<template>
<div>
  <h3>Simulation settings</h3>
  <SimulationSettings
    :constituencies="vote_table.constituencies"
    :simulation_rules="simulation_rules"
    @update-rules="updateSimulationRules">
  </SimulationSettings>
  
  <div style="text-align: center; margin-bottom: 0.7em;
              margin-left:16px; margin-right:16px">
    <span v-if="simulation_done">
      <b-button
        size="lg"
        variant="success"
        :disabled="!simulation_done"
        @click="recalculate"
        >
        Start simulation
      </b-button>
    </span>
    <span v-if="!simulation_done">
      <b-button
        size="lg"
        variant="danger"
        :disabled="simulation_done"
        @click="checkstatus(true)"
        >
        Stop simulation
      </b-button>
    </span>
  </div>
  <div class="row" style="margin-bottom: 0.1em;
                          margin-left:20px; margin-right:20px">
    <b-col cols="12">
      <span v-if="!simulation_done">
        Time remaining: {{time_left}} s
      </span>
    </b-col>
    <b-col cols="12">
      <b-progress
        :value="current_iteration"
        :max="0"
        :animated="!simulation_done"
        :variant="simulation_done ? 'success':'primary'"
        show-value>
      </b-progress>
    </b-col>
    <b-col cols="2">
      
    </b-col>
  </div>
  
  <h3>Simulation results</h3>
  <b-alert :show="results.data.length == 0">
    Run simulation to get results.
  </b-alert>
  <div v-if="results.data.length > 0" style="margin-left:25px">
    <b-container style="margin-left:0px; margin-bottom:20px">
      <b-button
        class="mb-10"
        style="margin-left:0px"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download simulation results to local Excel xlsx-file"
        @click="saveSimulationResults">
        Download Excel file
      </b-button>
    </b-container>
    <p></p>
    <h4>Constituency seats</h4>
    <ResultMatrix
      v-for="(ruleset, idx) in results.data"
      :key="'const-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="ruleset.list_measures.const_seats.avg"
      :stddev="ruleset.list_measures.const_seats.std"
      :title="ruleset.name"
      round="2">
    </ResultMatrix>
    
    <h4>Adjustment seats</h4>
    <ResultMatrix
      v-for="(ruleset, idx) in results.data"
      :key="'adj-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="ruleset.list_measures.adj_seats.avg"
      :stddev="ruleset.list_measures.adj_seats.std"
      :title="ruleset.name"
      round="2">
    </ResultMatrix>
    
    <h4>Total seats</h4>
    <ResultMatrix
      v-for="(ruleset, idx) in results.data"
      :key="'total-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="ruleset.list_measures.total_seats.avg"
      :stddev="ruleset.list_measures.total_seats.std"
      :title="ruleset.name"
      round="2">
    </ResultMatrix>
    
    <h4>Quality measures</h4>
    <SimulationData
      :measures="results.measures"
      :list_deviation_measures="results.list_deviation_measures"
      :totals_deviation_measures="results.totals_deviation_measures"
      :standardized_measures="results.standardized_measures"
      :ideal_comparison_measures="results.ideal_comparison_measures"
      :methods="results.methods"
      :data="results.data"
      :testnames="results.testnames">
    </SimulationData>
  </div>
</div>
</template>

<script>
import ResultMatrix from './components/ResultMatrix.vue'
import SimulationSettings from './SimulationSettings.vue'
import SimulationData from './components/SimulationData.vue'

export default {
  props: {
    "server": {},
    "main_rules": {},
    "vote_table": {},
    // "election_rules": {},
    // "simulation_rules": {},
  },
  components: {
    ResultMatrix,
    SimulationSettings,
    SimulationData,
  },
  
  data: function() {
    return {
      election_rules: this.main_rules.election_rules,
      simulation_rules: this.main_rules.simulation_rules,
      simulation_done: true,
      current_iteration: 0,
      time_left: 0,
      iteration_time: 0,
      inflight: 0,
      results: { measures: [], methods: [], data: [], parties: [], e_rules: [] },
    }
  },
  methods: {
    updateSimulationRules: function(rules) {
      // console.log("Updating rules")
      // console.log("rules", rules)
      this.simulation_rules = rules
      this.$emit('update-main-rules', rules)
    },
    check_simulation: function() {
      this.checkstatus(false)
    },
    checkstatus: function(stop) {
      this.inflight++;
      this.$http.post('/api/simulate/check/', {
        sid: this.sid,
        stop: stop
      }).then(response => {
        this.inflight--;
        if (response.body.error) {
          console.log("Setting server errormsg 2")
          console.log("errormsg:", response.body.error);
          this.server.errormsg = response.body.error;
          this.server.waitingForData = false;
        } else {
          let status = response.body.status
          this.server.errormsg = '';
          this.server.error = false;
          this.simulation_done = status.done;
          this.current_iteration = status.iteration;
          this.iteration_time = status.iteration_time;
          this.time_left = status.time_left;
          this.results = response.body.results;
          this.server.waitingForData = false;
          if (this.simulation_done) {
            window.clearInterval(this.checktimer);
          }
        }
      }, response => {
        console.log("Setting server error 2")
        console.log("response.body", response.body)
        this.server.error = true;
        this.server.errormsg = 
        this.server.waitingForData = false;
      });
    },
    recalculate: function() {
      console.log("Starting simulation")
      this.current_iteration = 0
      this.results = { measures: [], methods: [], data: [] }
      this.sid = "";
      this.server.waitingForData = true;
      this.$http.post('/api/simulate/', {
        vote_table: this.vote_table,
        election_rules: this.election_rules,
        simulation_rules: this.simulation_rules,
      }).then(response => {
        if (response.body.error) {
          console.log("Setting server errormsg 3")
          this.server.error = true;
          this.server.errormsg = response.body.error;
          this.server.waitingForData = false;
        } else {
          this.server.errormsg = '';
          this.server.error = false;
          this.sid = response.body.sid;
          this.simulation_done = !response.body.started;
          this.server.waitingForData = false;
          // 250 ms between updating simulation progress bar
          this.checktimer = window.setInterval(this.check_simulation, 250);
        }
      }, response => {
        console.log("Setting server error 3")
        this.server.error = true;
        this.server.waitingForData = false;
      });
    },
    
    saveSimulationResults: function() {
      let promise = axios({
        method: "post",
        url: "/api/simdownload/",
        data: { sid: this.sid },
        responseType: "arraybuffer",
      });
      this.$emit("download-file", promise);
    }
  },
}
</script>
