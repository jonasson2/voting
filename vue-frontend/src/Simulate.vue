<template>
<div v-if="show_simulate">
  <h3>Simulation settings</h3>
  <b-modal id="upload-simulation-settings" ref="uploadSettingsDialog"
    title="Upload simulation settings">
    <p>Choose a simulation-settings JSON file created by Download.</p>
    <b-form-file v-model="settingsUploadFile" accept=".json"
      :state="Boolean(settingsUploadFile)" placeholder="Choose a file..."
      @input="loadSettings" />
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">Cancel</b-button>
    </template>
  </b-modal>
  <DownloadNameDialog id="simulation-settings-download-name"
    ref="settingsDownloadNameDialog" @confirm="confirmSettingsDownload" />
  <b-button-toolbar key-nav aria-label="Simulation settings tools"
    style="margin-left:12px; margin-bottom:12px">
    <b-button-group class="mx-1">
      <b-button v-b-modal.upload-simulation-settings class="mb-10"
        title="Upload simulation settings from a local JSON file">Upload</b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button class="mb-10" title="Download simulation settings to a local JSON file"
        @click="openSettingsDownload('settings')">Download</b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button class="mb-10" title="Restore the default simulation settings"
        @click="resetSimulationSettings">Reset to defaults</b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button v-b-modal.upload-all-dialog class="mb-10"
        title="Upload votes, electoral systems, and simulation settings from a local JSON file">Upload all</b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button class="mb-10"
        title="Download votes, electoral systems, and simulation settings to a local JSON file"
        @click="openSettingsDownload('all')">Download all</b-button>
    </b-button-group>
  </b-button-toolbar>
  <DownloadNameDialog
    id="simulation-results-download-name"
    ref="downloadNameDialog"
    @confirm="saveSimulationResults"
  />
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
  <div v-if="results.data.length == 0">
    <div v-if="usesPartyVotes() && !partyVotesValid()">
      <b-alert :show="true">
        <h4 class="alert-heading">Simulations cannot be conducted.</h4>
        All votes in National party votes and seats must be numbers if they are to be used to compute the total number of seats for each party
      </b-alert>
    </div>
  </div>
  <div v-else-if="results.data.length > 0" style="margin-left:25px">
    <b-container style="margin-left:0px; margin-bottom:20px">
      <b-button
        class="mb-10"
        style="margin-left:0px"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download simulation results to local Excel xlsx-file"
        @click="openDownload">
        Download Excel file
      </b-button>
    </b-container>
    <p></p>
    <h4 style="..."
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Reference seat shares are fractional benchmarks calculated from
        the simulated votes using the selected scaling."
        >Quality measures</h4>
    <QualityMeasures
      :vuedata="vuedata"
      :stats="vuedata.stats"
      :stat_headings="vuedata.stat_headings"
      :system_names="vuedata.system_names"
      :group_ids="vuedata.group_ids"
      :group_titles="vuedata.group_titles"
      :footnotes="vuedata.footnotes"
      :show="vuedata.show"
      >
      </QualityMeasures>
  </div>
</div>
</template>

<script>
import SimulationSettings from './SimulationSettings.vue'
// import SimulationData from './components/SimulationData.vue'
import QualityMeasures from './components/QualityMeasures.vue'
import DownloadNameDialog from './components/DownloadNameDialog.vue'
import {
  canChooseSaveLocation, chooseSaveLocation, downloadBasename,
  downloadFilename, timestampedDownloadBasename,
} from './downloadName.js'
import { mapState, mapActions, mapMutations } from 'vuex';

export default {
  computed: {
    ...mapState([
      'vote_table',
      'systems',
      'sim_settings',
      'show_simulate',
      'simulateCreated',
      'display_settings',
      'all_filename',
      'all_file_handle',
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
      vuedata: {},
      settingsUploadFile: null,
      settingsDownloadKind: null,
    }
  },
  components: {
    SimulationSettings,
    QualityMeasures,
    DownloadNameDialog,
    // SimulationData,
  },
  methods: {
    ...mapMutations([
      "serverError",
      "clearServerError",
      "addBeforeunload"
    ]),
    ...mapActions([
      "downloadFile", "saveAll", "uploadSimulationSettings",
      "resetSimulationSettings"
    ]),
    loadSettings(file) {
      if (!file) return
      this.$refs.uploadSettingsDialog.hide()
      const formData = new FormData()
      formData.append('file', file, file.name)
      this.uploadSimulationSettings(formData)
      this.settingsUploadFile = null
    },
    async openSettingsDownload(kind) {
      this.settingsDownloadKind = kind
      const prefix = kind === 'all' ? 'simulator' : 'simulation-settings'
      const basename = kind === 'all'
        ? (downloadBasename(this.all_filename, 'json')
          || timestampedDownloadBasename(prefix))
        : timestampedDownloadBasename(prefix)
      if (canChooseSaveLocation()) {
        try {
          const fileHandle = await chooseSaveLocation(basename, 'json',
            kind === 'all' ? this.all_file_handle : null)
          this.confirmSettingsDownload({fileHandle})
          return
        } catch (error) {
          if (error.name === 'AbortError') return
        }
      }
      if (kind === 'all' && this.all_filename) {
        this.confirmSettingsDownload({filename: downloadFilename(basename, 'json')})
        return
      }
      this.$refs.settingsDownloadNameDialog.open(basename, 'json')
    },
    confirmSettingsDownload(destination) {
      if (this.settingsDownloadKind === 'all') {
        this.saveAll(destination)
        return
      }
      const promise = axios({
        method: 'post', url: 'api/simulation-settings/save/',
        data: {sim_settings: this.sim_settings}, responseType: 'arraybuffer',
      })
      this.downloadFile({promise, ...destination})
    },
    check_simulation: function() {
      this.checkstatus(false)
    },
    finish_simulation: function(response) {
      this.simulation_done = true;
      window.clearInterval(this.checktimer);
    },
    checkstatus: function(stop) {
      console.log("checking simulation:", this.simid, timeStamp())
      this.$http.post('api/simulate/check/', {
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
      this.$http.post('api/simulate/', {
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
      
    openDownload() {
      const basename = timestampedDownloadBasename('simulation')
      this.$refs.downloadNameDialog.open(basename, 'xlsx')
    },
    saveSimulationResults: function(destination) {
      let promise = axios({
        method: "post",
        url: "api/simdownload/",
        data: {
          simid: this.simid,
          display_settings: this.display_settings,
        },
        responseType: "arraybuffer",
      });
      this.downloadFile({promise, ...destination})
    },
    usesPartyVotes: function() {
      return this.vote_table.party_vote_info.specified
        && ['party_vote_info', 'average'].includes(this.vote_table.party_vote_basis)
    },
    partyVotesValid: function() {
      return this.vote_table.party_vote_info.votes.every(function(element) {return typeof element == 'number';})
    },
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
