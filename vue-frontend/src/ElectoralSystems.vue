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
  <b-tabs
    v-if="!adding_system"
    :key="`${systems.length}:${activeSystemIndex}`"
    v-model="activeTabIndex"
    no-key-nav
    card
    >
    <b-tab
      v-for="sysidx in system_numbering"
      :key="sysidx"
      :title-link-class="sysidx == -3 ? 'system-delete-tab' : null"
      @click="handleTabClick(sysidx)"
      >
      <template v-if="sysidx==-2" #title>
        <span
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Reorder systems"
          >←</span>
      </template>
      <template v-else-if="sysidx==-1" #title>
        <span
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Reorder systems"
          >→</span>
      </template>
      <template v-else-if="sysidx==-3" #title>
        <span
          class="system-delete-symbol"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Remove selected electoral system"
          >X</span>
      </template>
      <template v-else #title>
        {{systemName(sysidx)}}
      </template>
      <template v-if="systems[sysidx]">
        <b-form-group
          label-for="input-horizontal"
          label-cols="auto"
          label="System name"
          >
          <b-form-input
            class="pt-0 pb-0"
            style="font-weight:bold; margin-top:-4px; font-size:110%; width:100%;"
            v-model="systems[sysidx].name"
            :state="systemNameState(sysidx)"
            required
            v-autowidth="{ maxWidth: '500px', minWidth: '1px' }"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Enter electoral system name"
            />
        </b-form-group>
        <b-alert :show="Boolean(systemNameError)">
        {{systemNameError}}
        </b-alert>
        <ElectionSettings
          :systemidx="sysidx"
          :capabilities="capabilities"
          :adding_system="adding_system"
        >
        </ElectionSettings>
      </template>
    </b-tab>
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
        return this.system_numbering.indexOf(this.activeSystemIndex)
      },
      set() {}
    },
    activeSystemIndex: {
      get() {
        return this.$store.state.activeSystemIndex
      },
      set(val) {
        this.setActiveSystemIndex(val)
      }
    },
    systemNameError() {
      const names = this.systems.map(system => system.name)
      if (names.some(name => typeof name !== "string" || !name.trim())) {
        return "Electoral system names cannot be blank"
      }
      if (new Set(names).size !== names.length) {
        return "All system names should be unique"
      }
      return ""
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
    systemName(sysidx) {
      return this.systems[sysidx] ? this.systems[sysidx].name : ""
    },
    systemNameState(sysidx) {
      const name = this.systemName(sysidx)
      return typeof name === "string" && name.trim() ? null : false
    },
    handleTabClick(sysidx) {
      if (sysidx == -3) this.deleteCurrentSystem()
      else this.reorder(sysidx)
    },
    swap(a,i) {
      [a[i], a[i+1]] = [a[i+1], a[i]]
    },
    reorder(sysidx) {
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
