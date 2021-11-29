<template>
<div v-if="show_systems">
  <b-modal
    size="lg"
    id="modaluploadesettings"
    title="Upload JSON file"
    @ok="uploadSystems"
    >
    <p v-if="replace">
      The file provided must be a JSON file formatted like a file downloaded
      from here, using the Save button. The electoral systems contained in the
      file will be replace the current systems.
    </p>
    <p v-else>
      The file provided must be a JSON file formatted like a file downloaded
      from here, using the Save button. The electoral systems contained in the
      file will be added to those currently specified.
    </p>
    <b-form-file
      v-model="uploadfile"
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      >
    </b-form-file>
  </b-modal>
  <b-button-toolbar key-nav aria-label="Electoral settings tools"
                    style="margin-left:12px">
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title = "Upload electoral system settings from local file"
        v-b-modal.modaluploadesettings
        @click = setReplace(true)
        >
        Load from file
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title = "Append electoral systems by uploading settings
                 from local file"
        v-b-modal.modaluploadesettings
        @click = setReplace(false)
        >
        Append from file
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download settings for all electoral systems to local
               json-file. Also saves simulation settings" 
        @click="saveSettings()"
        >
        Save
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <br>
  <b-tabs v-if="!adding_system" v-model="activeSystemIndex" card>
    <b-tab v-for="(system, idx) in systems" :key="idx">
      <!-- <template v-if="idx==activeTabIndex - 1" #title> -->
      <!--   ← -->
      <!-- </template> -->
      <!-- <template v-else-if="idx==activeTabIndex + 1" #title> -->
      <!--   → -->
      <!-- </template> -->
      <!-- <template v-else v-slot:title> -->
      <!--   {{system.name}} -->
        <!-- </template> -->
      <template #title> {{system.name}} </template>
      <b-input-group>
        <b-input
          class="mb-3"
          v-model="system.name"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-input-group>
      <ElectionSettings
        :systemidx="idx"
        :capabilities="capabilities"
        >
      </ElectionSettings>
    </b-tab>
    <template #tabs-start>
      <b-button
        size="sm"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Remove selected electoral system"
        @click="deleteSystem(activeSystemIndex)"
        >
        <b>X</b>
      </b-button>
    </template>
    <template #tabs-end>
      <b-button
        size="sm"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Add electoral system"
        @click="addNewSystem">
        <b>+</b>
      </b-button>
    </template>
    <div slot="empty">
      There are no electoral systems specified.
      Use the <b>+</b> button to create a new electoral system.
    </div>
  </b-tabs>
</div>
</template>

<script>
import ElectionSettings from './ElectionSettings.vue'
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
  components: {
    ElectionSettings,
  },
  
  computed: {
    ...mapState([
      'vote_table',
      'sim_settings',
      'systems',
      'show_systems'
    ]),
  },
  
  data: function() {
    return {
      idx: 0,
      system: {},
      dsystems: [{}],
      activeTabIndex: 0,     // Includes the <-- and --> tabs
      activeSystemIndex: 0,  // Not including the <-- and --> tabs
      replace: false,
      uploadfile: null,
      adding_system: false,
      created: false
    }
  },
    
  methods: {
    ...mapMutations([
      "addSystem",
      "addSysConst",
      "updateSysConst",
      "updateSimSettings",
      "deleteSystem",
      "deleteAllSystems",
      "setWaitingForData",
      "clearWaitingForData",
      "addBeforeunload"
    ]),
    ...mapActions([
      "downloadFile",
      "uploadElectoralSystems"
    ]),
    setReplace: function(status) {
      this.replace = status
    },
    updateDisplaySystems() {
      // dsystems exists to allow reordering of systems
      let i, n=this.systems.length
      console.log("updateDisplaySystems, n=", n)
      this.dsystems = []
      for (i=0; i < n; i++) {
        if (n > 1 && i > 0 && i == this.activeSystemIndex) {
          console.log("pushing left arrow")
          this.dsystems.push([])
        }
        this.dsystems.push(this.systems[i])
        if (n > 1 && i < n-1 && i == this.activeSystemIndex) {
          console.log("pushing right arrow")
          this.dsystems.push([])
        }
      }
      this.activeTabIndex = this.activeSystemIndex + 1
      console.log("end of updateDisplaySystems")
    },
    saveSettings: function () {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/settings/save",
        data: {
          systems:        this.systems,
          sim_settings:   this.sim_settings,
        },
        responseType: "arraybuffer",
      });
      console.log("NAME: ",this.$options.name)
      this.downloadFile(promise)
    },
    uploadSystems: function(evt) {
      if (!this.uploadfile) evt.preventDefault();
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      console.log("replace", this.replace)
      console.log("formData", formData)
      this.uploadElectoralSystems({"formData":formData, "replace":this.replace})
    },
    addNewSystem() {
      this.adding_system = true
      this.setWaitingForData()
      this.$http.post(
        '/api/capabilities',
        this.vote_table.constituencies,
      ).then(response => {
        let r = response.body
        this.capabilities = r.capabilities;
        this.addSystem(r.election_system)
        this.updateSimSettings(r.sim_settings)
        this.activeSystemIndex += 1
        this.$store.dispatch("recalc_sys_const")
        this.adding_system = false
        this.clearWaitingForData()
        this.$nextTick(()=>{this.created = true})
        console.log("added systems")
      })
    }
  },
  created: function () {
    console.log("CreatedElectoralSystems")
    this.addNewSystem()
  },
  watch: {
    systems: {
      handler() { if (this.created) this.addBeforeunload() },
      deep: true
    }
  },
}
</script>
