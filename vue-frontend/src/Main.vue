<!-- https://stackoverflow.com/questions/61497825/bootstrap-vue-custom-border-column-style-and-custom-border-row-style-on-b-table -->

<template>
  <div>
  <b-modal id="upload-all-dialog" ref="uploadAllDialog"
    size="lg" title="Upload votes, electoral systems, and simulation settings">
    <p>Choose a JSON file created by Download all.</p>
    <b-form-file v-model="allUploadFile" accept=".json"
      :state="Boolean(allUploadFile)" placeholder="Choose a file..."
      @input="loadAll" />
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">Cancel</b-button>
    </template>
  </b-modal>
  <b-navbar toggleable="md" type="dark" variant="info" sticky>
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <b-alert
    :show="server_error != ''"
    dismissible
    @dismissed="clearServerError()"
    variant="danger"
    >
    <template v-for="(line, idx) in server_error">
      <br v-if="idx>0">
      {{line}}
    </template>
  </b-alert>
  <b-tabs
    nav-class="simulator-tabs"
    active-nav-item-class="font-weight-bold"
    no-key-nav card
    >
    <b-tab title="Source votes and seats" active @click="showVoteMatrix">
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        >
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems" @click="showElectoralSystems">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems>
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election" @click="showElection">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->      
      <Election>
      </Election>
    </b-tab>
    <b-tab title="Simulated elections" @click="showSimulate()">
      <!-- <P>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate>
      </Simulate>
    </b-tab>
    <b-tab title="Settings">
      <Settings />
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
import VoteMatrix from './VoteMatrix.vue'
import Intro from './Intro.vue'
import Settings from './Settings.vue'
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
  data() {
    return { allUploadFile: null }
  },
  components: {
    VoteMatrix,
    Election,
    Simulate,
    ElectoralSystems,
    Intro,
    Settings,
  },
  
  computed: {
    ...mapState([
      'server_error'
    ]),
  },
  //computed: mapState(['server_error']),

  methods: {
    ...mapMutations([
      "clearServerError",
      "showVoteMatrix",
    ]),
    ...mapActions([
      "uploadAll",
      "showElection",
      "showElectoralSystems",
      "showSimulate",
      "initialize"
    ]),
    showHelp: function() {
      window.open("static/leidbeiningar.pdf", "_blank");
    },
    loadAll(file) {
      if (!file) return
      this.$refs.uploadAllDialog.hide()
      const formData = new FormData()
      formData.append("file", file, file.name)
      this.uploadAll({formData, filename: file.name})
      this.allUploadFile = null
    },
  },
  mounted: function() {
    console.log("Main created")
    this.initialize()
  },
}
</script>
