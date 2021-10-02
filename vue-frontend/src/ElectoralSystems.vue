<template>
<div>
  <b-modal
    size="lg"
    id="modaluploadesettings"
    title="Upload JSON file"
    @ok="uploadSettingsAndAppend"
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
  <b-modal
    size="lg"
    id="modaluploadesettingsreplace"
    title="Upload JSON file"
    @ok="uploadSettingsAndReplace"
    >
    <p>
      The file provided must be a JSON file
      formatted like a file downloaded from here, using the Save button.
      The electoral systems contained in the file
      will replace those you have already specified.
    </p>
    <b-form-file
      ref="replaceFromFile"
      v-model="uploadfile"
      :state="Boolean(uploadfile)"
      placeholder="Choose a file..."
      >
    </b-form-file>
  </b-modal>
  <b-modal
    size="lg"
    id="modalsaveesettings"
    title="Download JSON file"
    @ok="newSaveESettings"
    >
    <p>
      All current electoral system settings will be saved to a
      JSON file.
    </p>
    <b-form-file
      :directory=true
      ref="saveToFile"
      v-model="savefolder"
      :state="Boolean()"
      placeholder="Select folder..."
      >
    </b-form-file>
  </b-modal>
  <b-button-toolbar key-nav aria-label="Electoral settings tools" style="margin-left:12px">
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Remove all electoral systems"
        @click="deleteAllElectionRules()"
        >
        Clear
      </b-button>
    </b-button-group>
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title = "Add electoral systems by uploading settings from local file"
        v-b-modal.modaluploadesettings
        >
        Add from file
      </b-button>
    </b-button-group>
    <!-- <b-button-group class="mx-1"> -->
      <!--   <b-button -->
      <!--     class="mb-10" -->
      <!--     v-b-tooltip.hover.bottom.v-primary.ds500 -->
      <!--     title = "Download settings for all electoral systems to local file" -->
      <!--     v-b-modal.modalsaveesettings -->
      <!--     > -->
        <!--     Save -->
        <!--   </b-button> -->
      <!-- </b-button-group> -->
    <b-button-group class="mx-1">
      <b-button
        class="mb-10"
        v-b-tooltip.hover.bottom.v-primary.ds500
        title="Download settings for all electoral systems to local json-file. You may need to change browser settings; see Help for details"
        @click="saveSettings()"
        >
        Save
      </b-button>
    </b-button-group>
  </b-button-toolbar>
  <br>
  <b-tabs v-model="activeTabIndex" card>
    <b-tab v-for="(rules, rulesidx) in election_rules" :key="rulesidx">
      <template v-slot:title>
        {{rules.name}}
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
          v-model="rules.name"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Enter electoral system name"
          />
      </b-input-group>
      <ElectionSettings
        :rulesidx="rulesidx"
        :rules="rules"
        @update-rules="updateElectionRules">
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
  
  props: {
    "server": {default: {
      waitingForData: false,
      errormsg: '',
      error: false,
    }},
    "election_rules": {default: [{}]},
    "simulation_rules": {default: [{}]},
  },
  
  data: function() {
    return {
      activeTabIndex: 0,
      uploadfile: null,
      savefolder: null,
    }
  },
  
  created: function() {
    console.log("Created ElectoralSystems");
    console.log("rules", this.election_rules);
  },
  
  methods: {
    addElectionRules: function() {
      console.log("addElectionRules called");
      this.election_rules.push({})
    },
    deleteElectionRules: function(idx) {
      console.log("deleting election rules", idx);
      this.election_rules.splice(idx, 1);
    },
    deleteAllElectionRules: function() {
      console.log("deleting all rules");
      for (var i=this.election_rules.length-1; i>=0; i--) {
        console.log("deleting rules #", i);
        this.deleteElectionRules(i);
      }
    },
    updateElectionRules: function(rules, idx) {
      console.log("Call updateElectionRules in ElectoralSystems")
      if (rules.name == "System") rules.name += "-" + (idx+1).toString();
      this.activeTabIndex = idx;
      console.log("rules", rules);
      //this.$set(this.election_rules, idx, rules);
      this.$emit('update-main-election-rules', rules, idx);
      //this works too: this.election_rules.splice(idx, 1, rules);
    },
    updateElectionRulesAndActivate: function(rules, idx) {
      console.log("updateElectionRulesAndActivate");
      this.updateElectionRules(rules, idx);
      this.activeTabIndex = idx;
    },
    saveSettings: function() {
      let promise = axios({
        method: "post",
        url: "/api/settings/save",
        data: {
          e_settings: this.election_rules,
          sim_settings: this.simulation_rules
        },
        responseType: "arraybuffer",
      });
      this.$emit("download-file", promise);
    },
    uploadSettingsAndAppend: function(evt) {
      var replace = false;
      this.uploadSettings(evt, replace);
      this.$refs['appendFromFile'].reset();
    },
    uploadSettingsAndReplace: function(evt) {
      var replace = true;
      this.uploadSettings(evt, replace);
      this.$refs['replaceFromFile'].reset();
    },
    newSaveESettings: function(evt) {
      console.log("newSaveESettings called");
      console.log("evt=", evt);
    },    
    uploadSettings: function(evt, replace) {
      if (!this.uploadfile) {
        evt.preventDefault();
      }
      var formData = new FormData();
      formData.append('file', this.uploadfile, this.uploadfile.name);
      this.$http.post('/api/settings/upload/', formData).then(response => {
        if (replace){
          this.election_rules = [];
        }
        for (const setting of response.data.e_settings){
          this.election_rules.push(setting);
        }
        if (response.data.sim_settings){
          this.simulation_rules = response.data.sim_settings;
        }
      });
    },
  }
}
</script>
