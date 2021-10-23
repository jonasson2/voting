<<template>
<div  v-if="vote_table_constituencies.length > 0">
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
  <b-tabs v-model="activeTabIndex" card>
    <b-tab v-for="(system, systemidx) in systems" :key="systemidx">
      <template v-slot:title>
        {{system.name}}
      </template>
      <b-input-group>
        <template>
          <b-button
            style="margin-bottom:10px;margin-left:-5px"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title = "Remove electoral system"
            size="sm"
            variant="link"
            @click="deleteElectionRules(systemidx)">
            X
          </b-button>
        </template>
        <b-input
          class="mb-3"
          v-model="system.name"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-input-group>
      <ElectionSettings
        :newSystem="system"
        :systemidx="systemidx"
        :vote_table_constituencies="vote_table_constituencies"
        ref="systemref"
        @update-system="updateSystem"
        @update-sim-settings="updateSimSettings"
        >
      </ElectionSettings>
    </b-tab>
    <template v-slot:tabs-end>
      <b-button
        size="sm"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Add electoral system"
        @click="addElectionRules">
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

export default {
  components: {
    ElectionSettings,
  },
  
  props: [
    "sim_settings",
    "vote_table_constituencies",
    "matrix"
  ],
  
  data: function() {
    return {
      systems: [{}],
      activeTabIndex: 0,
      replace: false,
      uploadfile: null,
      savefolder: null,
    }
  },
  
  methods: {
    getNewRules: function(election_rules, passToSettings) {
      this.systems = election_rules
      if (passToSettings) passToSettings(this.systems[this.activeTabIndex])
    },
    setReplace: function(status) {
      this.replace = status
    },
    addElectionRules: function() {
      // ElectionSettings will fill the rule with data and emit update-system
      this.systems.push({})
    },
    deleteElectionRules: function(idx) {
      console.log("deleting election rule #", idx);
      this.systems.splice(idx, 1);
      this.$emit("update-rules", this.systems, this.getNewRules);
    },
    updateSimSettings: function(sim_settings) {
      console.log("Sending sim_settings to Main", sim_settings)
      this.$emit("update-simulation-settings", sim_settings);
    },
    updateSystem: function(system, idx, passToSettings) {
      if (system.name == "System") system.name += "-" + (idx+1).toString();
      this.activeTabIndex = idx;
      this.systems.splice(idx, 1, system);
      console.log("In updateSystem in ElectoralSystems")
      this.$emit("update-rules", this.systems, this.getNewRules, passToSettings);
    },
    saveSettings: function () {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/settings/save",
        data: {
          e_settings: this.systems,
          sim_settings: this.sim_settings
        },
        responseType: "arraybuffer",
      });
      console.log("NAME: ",this.$options.name)
      this.$emit("download-file", promise);
    },
    uploadSettings: function(evt) {
      if (!this.uploadfile) evt.preventDefault();
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.$http.post('/api/settings/upload/', formData).then(response => {
        if (this.replace){
          this.systems.splice(0, this.systems.length)
        }
        for (var i=0; i < response.data.e_settings.length; i++) {
          var setting = response.data.e_settings[i]
          this.systems.push(setting);
          console.log("Pushing, i=", i, ", name=", this.systems[i].name)
        }
        this.$emit("update-rules", this.systems);
        this.$emit("update-simulation-settings", response.data.sim_settings);
      });
    },
  },
  created: function () {
    console.log("CreatedElectoralSystems");
  },

}
</script>
