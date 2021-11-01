<template>
<div  v-if="vote_table.constituencies.length > 0">
  <b-modal
    size="lg"
    id="modaluploadesettings"
    title="Upload JSON file"
    @ok="uploadSettings"
    >
    <p>
      The file provided must be a JSON file
      formatted like a file downloaded from here, using the Save button.
      The electoral systems contained in the file
      will be added to those you have already specified.
    </p>
    <b-form-file
      ref="appendFromFile"
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
        title="Download settings for all electoral systems to local json-file. 
               You may need to change browser settings; see Help for details"
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
        @click="deleteSystem()">
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
import { mapState } from 'vuex';

export default {
  components: {
    ElectionSettings,
  },
  
  computed: mapState([
    'vote_table',
    'sim_settings',
    'systems',
    'sys_constituencies',
    'waiting_for_data'
  ]),
  
  data: function() {
    return {
      idx: 0,
      system: {},
      dsystems: [{}],
      activeTabIndex: 0,     // Includes the <-- and --> tabs
      activeSystemIndex: 0,  // Not including the <-- and --> tabs
      replace: false,
      uploadfile: null,
      adding_system: false
    }
  },
  
  watch: {
    systems: {
      handler: function (val) {
        //console.log("Watching systems", this.systems)
        //this.updateDisplaySystems()
      },
      deep: true
    },
  },
  
  methods: {
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
    deleteSystem: function() {
      console.log("deleting election rule #");
      this.$store.commit("deleteSystem", this.activeSystemIndex)
    },
    saveSettings: function () {
      console.log(">>>", this.sys_constituencies)
      let promise;
      promise = axios({
        method: "post",
        url: "/api/settings/save",
        data: {
          rules:          this.systems,
          sim_settings:   this.sim_settings,
          constituencies: this.sys_constituencies
        },
        responseType: "arraybuffer",
      });
      console.log("NAME: ",this.$options.name)
      this.$emit("download-file", promise);
    },
    uploadSettings: function(evt) {
      this.$store.commit('waiting')
      if (!this.uploadfile) evt.preventDefault();
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.$http.post('/api/settings/upload/', formData).then(response => {
        if (this.replace){
          this.$store.commit("deleteAllSystems")
          // this.systems.splice(0, this.systems.length)
          console.log("Clearing systems")
          console.log("waiting", this.waiting_for_data)
        }
        for (var i=0; i < response.data.rules.length; i++) {
          this.$store.commit("addSystem", response.data.rules[i])
        }
        this.$store.commit("updateSysConst", response.data.constituencies)
        //this.updateDisplaySystems()
        console.log("this.dsystems", this.dsystems)
        this.$store.commit("updateSimSettings", response.data.sim_settings);
        this.$store.dispatch("recalc_sys_const")
        this.$store.commit('notWaiting')
      });
    },
    addNewSystem() {
      this.$store.commit('waiting')
      this.adding_system = true
      this.$http.post(
        '/api/capabilities',
        this.vote_table.constituencies,
      ).then(response => {
        let r = response.body
        this.capabilities = r.capabilities;
        console.log("in addNewSystem")
        console.log("r.election_rules", r.election_rules)
        console.log("r.const", r.constituencies)
        this.$store.commit("addSystem", r.election_rules)
        this.$store.commit("addSysConst", r.constituencies)
        this.$store.commit("updateSimSettings", r.sim_settings)
        console.log("this.sys_constituencies", this.sys_constituencies)
        this.activeSystemIndex += 1
        this.$store.dispatch("recalc_sys_const")
      }),
      this.$store.commit('notWaiting')
      this.adding_system = false
    }
  },
  created: function () {
    console.log("CreatedElectoralSystems")
    this.addNewSystem()
  }
}
</script>
