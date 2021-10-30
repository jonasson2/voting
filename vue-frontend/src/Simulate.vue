<template>
<div>
  <h3>Simulation settings</h3>
  <SimulationSettings
    :constituencies="election_rules[0].constituencies"
    :sim_settings="settings"
    @update-sim-settings="updateSimSettings"
    >
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
      <b-progress
        height="30px"
        :max="settings.simulation_count"
        :animated="!simulation_done">
        <b-progress-bar
          :variant="simulation_done ? 'success':'primary'"
          :value="current_iteration">
          <span style="font-size:150%">{{current_iteration}}</span>
        </b-progress-bar>
      </b-progress>
    </b-col>
    <b-col cols="12">
      <span v-if="!simulation_done">
        time remaining: {{time_left}}
      </span>
      <span v-if="simulation_done">
        time remaining: {{time_left}}, simulation time: {{total_time}}
      </span>
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
      :round="2">
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
      :round="2">
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
      :round="2">
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
  props: [
    "vote_table",
    "election_rules",
    "sim_settings",
  ],
  data: function() {
    return {
      settings: {},
      simulation_done: true,
      current_iteration: 0,
      time_left: 0,
      total_time: 0,
      inflight: 0,
      watching: true,
      results: { measures: [], methods: [], data: [], parties: [], e_rules: [] }
    }
  },
  components: {
    ResultMatrix,
    SimulationSettings,
    SimulationData,
  },
  watch: {
    sim_settings: {
      handler: function(val) {
        if (this.watching) this.settings = val
      },
      deep: true
    }
  },
  methods: {
    updateSimSettings: function(settings) {
      this.watching = false
      this.settings = settings
      this.$nextTick(()=>{this.watching = true})
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
          this.$emit("server-error", response.body.error)
        } else {
          let status = response.body.status
          this.simulation_done = status.done;
          this.current_iteration = status.iteration;
          this.total_time = status.total_time;
          this.time_left = status.time_left;
          this.results = response.body.results;
          if (this.simulation_done) {
            window.clearInterval(this.checktimer);
          }
        }
      }, response => {
        this.$emit("server-error", response.body)
      });
    },
    recalculate: function() {
      console.log("Starting simulation")
      this.current_iteration = 0
      this.results = { measures: [], methods: [], data: [] }
      this.sid = "";
      console.log("Simulate (recalculate): this.settings = ", this.settings)
      this.$http.post('/api/simulate/', {
        vote_table: this.vote_table,
        election_rules: this.election_rules,
        sim_settings: this.settings,
      }).then(response => {
        if (response.body.error) {
          this.$emit("server-error", response.body.error)          
        } else {
          this.sid = response.body.sid;
          this.simulation_done = !response.body.started;
          // 250 ms between updating simulation progress bar
          this.checktimer = window.setInterval(this.check_simulation, 250);
        }
      }, response => {
        this.$emit("server-error", response.body)          
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
