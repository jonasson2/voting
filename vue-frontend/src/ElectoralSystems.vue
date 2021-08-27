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
      ></b-form-file>
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
      ></b-form-file>
    </b-modal>
    <b-button-toolbar key-nav aria-label="Electoral settings tools">
      <b-button-group class="mx-1">
        <b-button
          title="Save current settings to file"
          @click="saveSettings()"
        >
          Save all
        </b-button>
      </b-button-group>
      <b-button-group class="mx-1">
        <b-button
          title="Upload additional settings from file (.json)"
          v-b-modal.modaluploadesettings
        >
          Upload
        </b-button>
        <b-button
          title="Upload new settings from file (.json), replacing the current settings"
          v-b-modal.modaluploadesettingsreplace
        >
          Replace
        </b-button>
      </b-button-group>
    </b-button-toolbar>
    <b-card no-body>
      <b-tabs v-model="activeTabIndex" card>
        <b-tab v-for="(rules, rulesidx) in election_rules" :key="rulesidx">
          <div slot="title">
            <b-button
              size="sm"
              variant="link"
              @click="deleteElectionRules(rulesidx)"
            >
              x
            </b-button>
            {{rulesidx+1}}-{{rules.name}}
          </div>
          <ElectionSettings
            :rulesidx="rulesidx"
            :rules="rules"
            @update-rules="updateElectionRules">
          </ElectionSettings>
        </b-tab>
        <template v-slot:tabs-end>
          <b-button size="sm" @click="addElectionRules"><b>+</b></b-button>
        </template>
        <div slot="empty">
          There are no electoral systems specified.
          Use the <b>+</b> button to create a new electoral system.
        </div>
      </b-tabs>
    </b-card>

  </div>
</template>

<script>
import ElectionSettings from './components/ElectionSettings.vue'

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
  },

  data: function() {
    return {
      activeTabIndex: 0,
      uploadfile: null,
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
      this.election_rules.splice(idx, 1);
    },
    updateElectionRules: function(rules, idx) {
      console.log("Call updateElectionRules in ElectoralSystems")
      console.log("rules", rules);
      this.$set(this.election_rules, idx, rules);
      //this works too: this.election_rules.splice(idx, 1, rules);
    },
    saveSettings: function() {
      this.$http.post('/api/settings/save/', {
        e_settings: this.election_rules,
        sim_settings: this.simulation_rules,
      }).then(response => {
        if (response.body.error) {
          this.server.errormsg = response.body.error;
          //this.$emit('server-error', response.body.error);
        } else {
          let link = document.createElement('a')
          link.href = '/api/downloads/get?id=' + response.data.download_id
          link.click()
        }
      }, response => {
        console.log("Error:", response);
      })
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
