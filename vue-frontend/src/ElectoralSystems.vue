<template>
<div>
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
    <b-tab v-for="(election_rule, rulesidx) in rules.election_rules" :key="rulesidx">
      <template v-slot:title>
        {{election_rule.name}}
      </template>
      <b-input-group>
        <template>
          <b-button
            style="margin-bottom:10px;margin-left:-5px"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title = "Remove electoral system"
            size="sm"
            variant="link"
            @click="deleteElectionRules(rulesidx)">
            X
          </b-button>
        </template>
        <b-input
          class="mb-3"
          v-model="election_rule.name"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-input-group>
      <ElectionSettings
        :rulesidx="rulesidx"
        :system="election_rule"
        :constituencies="constituencies"
        :waitingForData="waitingForData"
        :key="reRenderElectionSettings"
        @update-single-rules="updateSingleRules"
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
    "constituencies",
    "waitingForData"
  ],
  
  data: function() {
    return {
      rules: {
        election_rules: [{}],
        simul_settings: {}
      },
      activeTabIndex: 0,
      replace: false,
      uploadfile: null,
      savefolder: null,
      watching: true,
      reRenderElectionSettings: 0
    }
  },
  
  methods: {
    setReplace: function(status) {
      console.log("CALLED setReplace, status=",status)
      this.replace = status
    },
    addElectionRules: function() {
      console.log("addElectionRules called");
      this.rules.election_rules.push({})
    },
    deleteElectionRules: function(idx) {
      console.log("deleting election rule #", idx);
      this.rules.election_rules.splice(idx, 1);
      this.$emit("update-main-rules", this.rules);
    },
    addSystem: function(rules) {
      console.log("addSystem called")
      this.updateSingleRules(rules, this.rules.election_rules.length);
    },
    updateSingleRules: function(rules, idx, simul_settings) {
      console.log("rules.name=", rules.name)
      console.log("idx=", idx)
      if (rules.name == "System") rules.name += "-" + (idx+1).toString();
      this.activeTabIndex = idx;
      console.log("rules=",rules)
      this.$set(this.rules.election_rules, idx, rules);
      if (simul_settings) this.rules.simul_settings = simul_settings
      this.$emit("update-main-rules", this.rules);
    },
    saveSettings: function() {
      this.$emit("save-settings")
    },
    uploadSettings: function(evt) {
      console.log("CALLED uploadSettings");
      if (!this.uploadfile) {
        evt.preventDefault();
      }
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.$http.post('/api/settings/upload/', formData).then(response => {
        this.watching = false;
        console.log("this.replace", this.replace);
        if (this.replace){
          console.log("Deleting all rules")
          this.rules.election_rules.splice(0, this.rules.election_rules.length)
        }
        for (var i=0; i < response.data.e_settings.length; i++) {
          var setting = response.data.e_settings[i]
          this.addSystem(setting)
        }
        if (response.data.sim_settings){
          this.rules.simul_settings = response.data.sim_settings;
        }
        this.$emit("update-main-rules", this.rules);
        this.reRenderElectionSettings += 1;
      });
    },
  },
  created: function () {
    console.log("CreatedElectoralSystems");
  },

}
</script>
