<template>
<div v-if="show_systems && !waiting_for_data">
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
  <b-container style="margin-left:0px; margin-bottom:20px">
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
  </b-container>
  <b-tabs v-if="!adding_system" v-model="activeTabIndex" no-key-nav card>
    <b-tab v-for="(sysidx,idx) in system_numbering" :key="idx" @click="reorder(sysidx,idx)">
      <template v-if="sysidx==-2" #title>
        ←
      </template>
      <template v-else-if="sysidx==-1" #title>
        →
      </template>
      <template v-else v-slot:title>
        {{systems[sysidx].name}}
      </template>
      <b-input-group>
        <b-input
          class="mb-3"
          v-model="systems[activeSystemIndex].name"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-input-group>
      <ElectionSettings
        :systemidx="activeSystemIndex"
        :capabilities="capabilities"
        :adding_system="adding_system"
        >
      </ElectionSettings>
    </b-tab>
    <template #tabs-start>
      <b-button
        size="sm"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Remove selected electoral system"
        @click="deleteCurrentSystem"
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
      'system_numbering',
      'show_systems',
      'waiting_for_data'
    ]),
    activeTabIndex: {
      get() { return this.$store.state.activeTabIndex },
      set(val) { this.setActiveTabIndex(val) }
    },
    activeSystemIndex: {
      get() {
        let ati = this.activeTabIndex
        return ati == 0 ? ati : ati - 1
      }
    },
    tabCount: function() {
      return this.system_numbering.length
    },
  },
  
  data: function() {
    return {
      sysidx:0,
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
      "updateSimSettings",
      "deleteSystem",
      "deleteAllSystems",
      "setWaitingForData",
      "clearWaitingForData",
      "addBeforeunload",
      "newNumbering",
      "setActiveTabIndex",
    ]),
    ...mapActions([
      "downloadFile",
      "uploadElectoralSystems"
    ]),
    setReplace: function(status) {
      this.replace = status
    },
    swap(a,i) {
      [a[i], a[i+1]] = [a[i+1], a[i]]
    },
    reorder(sysidx,idx) {
      console.log("in reorder")
      console.log("idx", idx)
      console.log("sysidx", sysidx)
      console.log("activeTabIndex", this.activeTabIndex)
      console.log("activeSystemIndex", this.activeSystemIndex)
      let ati = this.activeTabIndex
      if (idx == ati)
        return
      else if (sysidx == -2) { // left arrow
        this.swap(this.systems, this.activeSystemIndex - 1)
        ati -= ati==2 ? 2 : 1
      }
      else if (sysidx == -1) { // right arrow
        this.swap(this.systems, this.activeSystemIndex)
        ati += ati==0 ? 2 : 1
      }
      else if (idx < ati)
        ati = idx + (idx==0 ? 0 : 1)
      else if (idx > ati)
        ati = idx - (idx==2 ? 0 : 1)
      this.setActiveTabIndex(ati)
      console.log("new activeTabIndex", ati)
      console.log("new activeSystemIndex", this.activeSystemIndex)
      this.newNumbering(this.activeSystemIndex)
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
      this.downloadFile(promise)
    },
    uploadSystems: function(evt) {
      if (!this.uploadfile) evt.preventDefault();
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.uploadElectoralSystems({"formData":formData, "replace":this.replace})
    },
    deleteCurrentSystem() {
      let asi = this.activeSystemIndex, nsys = this.systems.length
      if (asi == nsys - 1)
        this.setActiveTabIndex(this.activeTabIndex - (nsys > 1 ? 1 : 2))
      this.deleteSystem(this.activeSystemIndex)
    },
    addNewSystem() {
      this.setWaitingForData()
      this.adding_system = true
      let nsys = this.systems.length
      this.setActiveTabIndex(nsys == 0 ? 0 : nsys + 1)
      this.$http.post(
        '/api/capabilities',
        this.vote_table.constituencies,
      ).then(response => {
        let r = response.body
        this.capabilities = r.capabilities;
        this.addSystem(r.election_system)
        this.updateSimSettings(r.sim_settings)
        this.$store.dispatch("recalc_sys_const")
        this.$nextTick(()=>{
          this.created = true
          console.log("new system added")
          console.log("systems, system_numbering", this.systems, this.system_numbering)
          this.adding_system = false
          console.log("in addsys, new activeTabIndex", this.activeTabIndex)
        })
      })
    }
  },
  created: function () {
    console.log("CreatedElectoralSystems")
    console.log("systems", this.systems)
    this.deleteAllSystems()
    this.addNewSystem()
  },
  watch: {
    systems: {
      handler(val) {
        if (this.created && !this.adding_system && !this.waiting_for_data) this.addBeforeunload()
      },
      deep: true
    }
  },
}
</script>
