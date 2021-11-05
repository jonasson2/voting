<template>
<div v-if="show_simulate">
  <h3>Simulation settings</h3>
  <SimulationSettings />
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
        :max="sim_settings.simulation_count"
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
  <br>
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
      v-for="(system, idx) in results.data"
      :key="'const-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.const_seats.avg"
      :stddev="system.list_measures.const_seats.std"
      :title="system.name"
      :round="2">
    </ResultMatrix>
    <h4>Adjustment seats</h4>
    <ResultMatrix
      v-for="(system, idx) in results.data"
      :key="'adj-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.adj_seats.avg"
      :stddev="system.list_measures.adj_seats.std"
      :title="system.name"
      :round="2">
    </ResultMatrix>
    <h4>Total seats</h4>
    <ResultMatrix
      v-for="(system, idx) in results.data"
      :key="'total-seats-' + idx"
      :constituencies="results.e_rules[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.total_seats.avg"
      :stddev="system.list_measures.total_seats.std"
      :title="system.name"
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
import { mapState, mapMutations } from 'vuex';

export default {
  computed: {
    ...mapState([
      'vote_table',
      'systems',
      'sys_constituencies',
      'sim_settings',
      'show_simulate'
    ]),
  },
  created: function() {
    console.log("Created Simulate")
  },
  data: function() {
    return {
      simulation_done: true,
      current_iteration: 0,
      time_left: 0,
      total_time: 0,
      results: { measures: [], methods: [], data: [], parties: [], e_rules: [] }
    }
  },
  components: {
    ResultMatrix,
    SimulationSettings,
    SimulationData,
  },
  methods: {
    ...mapMutations([
      "serverError"
    ]),
    check_simulation: function() {
      this.checkstatus(false)
    },
    checkstatus: function(stop) {
      this.$http.post('/api/simulate/check/', {
        sid: this.sid,
        stop: stop
      }).then(response => {
        if (response.body.error) {
          this.serverError(response.body.error)
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
        this.serverError(response.body)
      });
    },
    recalculate: function() {
      console.log("Starting simulation")
      this.current_iteration = 0
      this.results = { measures: [], methods: [], data: [] }
      this.sid = "";
      console.log("Simulate (recalculate): this.sim_settings = ", this.sim_settings)
      this.$http.post('/api/simulate/', {
        vote_table:     this.vote_table,
        systems:          this.systems,
        sim_settings:   this.sim_settings,
        constituencies: this.sys_constituencies
      }).then(response => {
        if (response.body.error) {
          this.serverError(response.body.error)          
        } else {
          this.sid = response.body.sid;
          this.simulation_done = !response.body.started;
          // 250 ms between updating simulation progress bar
          this.checktimer = window.setInterval(this.check_simulation, 250);
        }
      }, response => {
        this.serverError(response.body)          
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
