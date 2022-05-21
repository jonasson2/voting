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
      Simulation time: {{total_time}}. Time remaining: {{time_left}}
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
    <h4 style="margin-bottom:0px">Quality measures</h4>
    <QualityMeasures
      :vuedata="vuedata"
      :stats="vuedata.stats"
      :stat_headings="vuedata.stat_headings"
      :system_names="vuedata.system_names"
      :group_ids="vuedata.group_ids"
      :group_titles="vuedata.group_titles"
      :footnotes="vuedata.footnotes"
      >
      </QualityMeasures>
    <h4>Constituency seats</h4>
    <SimResultMatrix
      v-for="(system, idx) in results.data"
      :key="'const-seats-' + idx"
      :constituencies="results.systems[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.const_seats.avg"
      :stddev="system.list_measures.const_seats.std"
      :title="system.name"
      :round="3">
    </SimResultMatrix>
    <h4>Adjustment seats</h4>
    <SimResultMatrix
      v-for="(system, idx) in results.data"
      :key="'adj-seats-' + idx"
      :constituencies="results.systems[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.adj_seats.avg"
      :stddev="system.list_measures.adj_seats.std"
      :title="system.name"
      :round="3">
    </SimResultMatrix>
    <h4>Total seats</h4>
    <SimResultMatrix
      v-for="(system, idx) in results.data"
      :key="'total-seats-' + idx"
      :constituencies="results.systems[idx].constituencies"
      :parties="results.parties"
      :values="system.list_measures.total_seats.avg"
      :stddev="system.list_measures.total_seats.std"
      :title="system.name"
      :round="3"
      >
    </SimResultMatrix>
  </div>
</div>
</template>

<script>
import SimResultMatrix from './components/SimResultMatrix.vue'
import SimulationSettings from './SimulationSettings.vue'
// import SimulationData from './components/SimulationData.vue'
import QualityMeasures from './components/QualityMeasures.vue'
import { mapState, mapActions, mapMutations } from 'vuex';

export default {
  computed: {
    ...mapState([
      'vote_table',
      'systems',
      'sim_settings',
      'show_simulate',
      'simulateCreated'
    ]),
    check_interval_ms: function() {
      // milliseconds between updating simulation progress bar
      return this.sim_settings.cpu_count > 1 ? 250 : 250
    },
    results_available: function() {
      if (typeof results !== "undefined") {
        console.log('results', results)
        console.log('results.data.length', results.data.length)
      }
      return typeof results !== "undefined" && results.data.length > 0
    }      
  },
  created: function() {
    console.log(timeStamp())
    console.log("Created Simulate")
  },
  data: function() {
    return {
      simulation_done: true,
      current_iteration: 0,
      time_left: 0,
      total_time: 0,
      results: {data: [], parties: [], systems: []},
      vuedata: {}
    }
  },
  components: {
    SimResultMatrix,
    SimulationSettings,
    QualityMeasures,
    // SimulationData,
  },
  methods: {
    ...mapMutations([
      "serverError",
      "clearServerError",
      "addBeforeunload"
    ]),
    ...mapActions([
      "downloadFile"
    ]),
    check_simulation: function() {
      this.checkstatus(false)
    },
    finish_simulation: function(response) {
      this.simulation_done = true;
      window.clearInterval(this.checktimer);
    },
    checkstatus: function(stop) {
      console.log("checking simulation:", this.simid, timeStamp())
      this.$http.post('/api/simulate/check/', {
        simid: this.simid,
        stop: stop
      }).then(response => {
        if (!response.body || response.body.error) {
          this.serverError(response.body)
          this.simulation_done = true;
          window.clearInterval(this.checktimer);
          console.log("simulation finished", timeStamp())
        } else {
          let status = response.body.status
          console.log("simulation status:", status, timeStamp())
          this.simulation_done = status.done;
          this.current_iteration = status.iteration;
          this.total_time = status.total_time;
          this.time_left = status.time_left;
          this.results = response.body.results
          if (this.results.data.length > 0) {
            console.log('results', this.results)
            this.vuedata = response.body.results.vuedata
            if (status.done) {
              console.log('finish simulation')
              this.finish_simulation()
            }
          }
        }
      })
    },
    recalculate: function() {
      console.log("Starting simulation")
      this.clearServerError()
      this.current_iteration = 0
      this.results = { measures: [], methods: [], data: [] }
      this.simid = "";
      console.log("Simulate (recalculate): this.sim_settings = ", this.sim_settings)
      this.$http.post('/api/simulate/', {
        vote_table:     this.vote_table,
        systems:        this.systems,
        sim_settings:   this.sim_settings,
      }).then(response => {
        if (!response.body || response.body.error) {
          this.finish_simulation()
          this.serverError(response.body) 
        } else {
          console.log("simulation started", timeStamp())
          this.simid = response.body.simid
          this.simulation_done = !response.body.started
          this.checktimer = window.setInterval(this.check_simulation,
                                               this.check_interval_ms)
          this.addBeforeunload()
        }
      });
    },
      
    saveSimulationResults: function() {
      let promise = axios({
        method: "post",
        url: "/api/simdownload/",
        data: { simid: this.simid },
        responseType: "arraybuffer",
      });
      this.downloadFile(promise)
    }
  },
  watch: {
    sim_settings: {
      handler() {
        if (this.simulateCreated) this.addBeforeunload()
      },
      deep: true
    }
  },  
}
function timeStamp(){
  var d = new Date();
  d = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2) + ':' +
    ('0' + d.getSeconds()).slice(-2) + '.' + ('00' + d.getMilliseconds()).slice(-3)
    return d
}
</script>
