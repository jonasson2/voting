<template>
<div v-show="show_systems && !waiting_for_data">
  <b-modal
    size="lg"
    id="modaluploadesettings"
    ref="modaluploadesettingsref"
    title="Upload JSON file"
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
      accept=".json"
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      @input="uploadSystems"
      >
    </b-form-file>
    <template #modal-footer="{ cancel }">
      <b-button size="sm" @click="cancel()">
        Cancel
      </b-button>
    </template>
  </b-modal>
  <DownloadNameDialog
    id="systems-download-name"
    ref="downloadNameDialog"
    @confirm="confirmDownload"
  />
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
        Upload
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
        @click="openDownload('settings')"
        >
        Download
      </b-button>
    </b-button-group>
        <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Upload vote table, all electoral systems, and simulation
               settings from local JSON file."
        v-b-modal.modaluploadall
        >
        Upload all
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download vote table, all electoral systems and simulation
               settings to local JSON file."
        @click="openDownload('all')"
        >
        Download all
      </b-button>
    </b-button-group>
  </b-button-toolbar>
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
      <b-form-group
        label-for="input-horizontal"
        label-cols="auto"
        label="System name"
        >
        <b-form-input
          class="pt-0 pb-0"
          style="font-weight:bold; margin-top:-4px; font-size:110%; width:100%;"
          v-model="systems[activeSystemIndex].name"
          v-autowidth="{ maxWidth: '500px', minWidth: '1px' }"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-form-group>
      <b-alert :show="showAlert()">
      All system names should be unique
      </b-alert>
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
        <span class="add-button-symbol">+</span>
      </b-button>
    </template>
    <template #empty>
      <div>
        There are no electoral systems specified.
        Use the <b>+</b> button to create a new electoral system.
      </div>
    </template>
  </b-tabs>
</div>
</template>

<script>
import DownloadNameDialog from './components/DownloadNameDialog.vue'
import ElectionSettings from './ElectionSettings.vue'
import {
  canChooseSaveLocation,
  chooseSaveLocation,
  timestampedDownloadBasename,
} from './downloadName.js'
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
  components: {
    DownloadNameDialog,
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
      get() {
        let asi = this.activeSystemIndex        
        return asi == 0 ? asi : asi + 1
      },
      set(val) {
        null
        //this.setActiveTabIndex(val)
      }
    },
    activeSystemIndex: {
      get() {
        return this.$store.state.activeSystemIndex
      },
      set(val) {
        this.setActiveSystemIndex(val)
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
      created: false,
      downloadKind: null,
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
      "serverError",
      "addBeforeunload",
      "newNumbering",
      "setActiveSystemIndex",
    ]),
    ...mapActions([
      "saveAll",
      "uploadAll",
      "downloadFile",
      "uploadElectoralSystems"
    ]),
    async openDownload(kind) {
      this.downloadKind = kind
      const prefix = kind === 'settings' ? 'electoral-systems' : 'simulator'
      const basename = timestampedDownloadBasename(prefix)
      if (canChooseSaveLocation()) {
        try {
          const fileHandle = await chooseSaveLocation(basename, 'json')
          this.confirmDownload({fileHandle})
          return
        } catch (error) {
          if (error.name === 'AbortError') return
        }
      }
      this.$refs.downloadNameDialog.open(basename, 'json')
    },
    confirmDownload(destination) {
      if (this.downloadKind === 'settings') this.saveSettings(destination)
      else this.saveAll(destination)
    },
    setReplace: function(status) {
      this.replace = status
    },
    swap(a,i) {
      [a[i], a[i+1]] = [a[i+1], a[i]]
    },
    reorder(sysidx,idx) {
      console.log("in reorderx<")
      console.log("idx", idx)
      console.log("sysidx", sysidx)
      console.log("activeTabIndex", this.activeTabIndex)
      console.log("activeSystemIndex", this.activeSystemIndex)
      let asi = this.activeSystemIndex
      if (sysidx == asi)
        return
      else if (sysidx == -2) { // left arrow
        this.swap(this.systems, this.activeSystemIndex - 1)
        asi -= 1
      }
      else if (sysidx == -1) { // right arrow
        this.swap(this.systems, this.activeSystemIndex)
        asi += 1
      }
      else
        asi = sysidx
      this.activeSystemIndex = asi
      this.newNumbering(this.activeSystemIndex)
      console.log("new activeSystemIndex", this.activeSystemIndex)
    },
    saveSettings: function (destination) {
      let promise;
      promise = axios({
        method: "post",
        url: "api/settings/save/",
        data: {
          systems:        this.systems,
          sim_settings:   this.sim_settings,
        },
        responseType: "arraybuffer",
      });
      this.downloadFile({promise, ...destination})
    },
    uploadSystems: function(file) {
      if (!file) return
      this.$refs.modaluploadesettingsref.hide()
      var formData = new FormData();
      formData.append('file', file, file.name);
      this.uploadElectoralSystems({"formData":formData, "replace":this.replace})
    },
    deleteCurrentSystem() {
      this.deleteSystem(this.activeSystemIndex)
    },
    addNewSystem() {
      this.setWaitingForData()
      this.adding_system = true
      let nsys = this.systems.length
      this.activeSystemIndex = nsys
      this.$http.post(
        'api/capabilities/',
        this.vote_table.constituencies,
      ).then(
        response => {
          let r = response.body
          if (!r || r.error) {
            this.serverError(r)
            this.adding_system = false
            this.clearWaitingForData()
            return
          }
          this.capabilities = r.capabilities;
          this.addSystem(r.election_system)
          this.updateSimSettings(r.sim_settings)
          this.$store.dispatch("recalc_sys_const")
          this.$nextTick(()=>{
            this.created = true
            this.adding_system = false
          })
        },
        response => {
          this.serverError(response.status)
          this.adding_system = false
          this.clearWaitingForData()
        }
      )
    },
    loadAll: function() {
      var formData = new FormData();
      formData.append("file", this.uploadfile, this.uploadfile.name);
      this.uploadAll(formData)
    },
    showAlert: function() {
      let names = this.systems.map(({ name }) => name)
      return new Set(names).size !== names.length
    },
  },
  created: function () {
    if (!this.systems.length) this.addNewSystem()
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
