<template>
<Div>
  <b-navbar toggleable="md" type="dark" variant="info">
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <b-alert
    :show="server.errormsg != ''"
    dismissible
    @dismissed="server.errormsg=''"
    variant="danger"
    >
    Server error. {{server.errormsg}}
  </b-alert>
  <b-tabs
    active-nav-item-class="font-weight-bold"
    card
    >
    <b-tab title="Votes and seats" active>
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        :vote_sums="vote_sums"
        @server-error="serverError"
        @download-file="downloadFile"
        @update-vote-table="updateVoteTable"
        >
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems
        :sim_settings="sim_settings"
        :vote_table_constituencies="vote_table_constituencies"
        :matrix="vote_table"
        @server-error="serverError"
        @update-rules="updateRules"
        @download-file="downloadFile"
        @update-simulation-settings="updateSimulationSettings"
        >
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election" @click = "recalculate()">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->      
      <Election
        :vote_table="vote_table"
        :election_rules="election_rules"
        :results="results"
        :waitingForData="waitingForData"
        @download-file="downloadFile"
        >
      </Election>
    </b-tab>
    <b-tab title="Simulated elections">
      <!-- <P>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate
        :vote_table="vote_table"
        :election_rules="election_rules"
        :sim_settings="sim_settings"
        @server-error="serverError"
        @download-file="downloadFile"
        >
      </Simulate>
    </b-tab>
    <b-tab title="Help">
      <Intro>
      </Intro>
    </b-tab>
  </b-tabs>
</b-card>
</div>
</template>

<script>
import Election from './Election.vue'
import ElectoralSystems from './ElectoralSystems.vue'
import Simulate from './Simulate.vue'
import VoteMatrix from './VoteMatrix.vue'
import Intro from './Intro.vue'

export default {
  components: {
    VoteMatrix,
    Election,
    Simulate,
    ElectoralSystems,
    Intro,
  },
  
  data: function() {
    return {
      server: {
        errormsg: '',
      },
      vote_table_constituencies: [],
      vote_table: {},
      vote_sums: {
        cseats: 0,
        aseats: 0,
        row: [],
        col: [],
        tot: 0,
      },
      election_rules: [{}],
      sim_settings: {},
      uploadfile: null,
      results: {},
      createdVotes: false,
      createdSettings: false,
      waitingForData: true,
    }
  },
  
  methods: {
    doneCreating: function() {
      return this.createdVotes && this.createdSettings
    },
    serverError: function(errormessage) {
      console.log("SERVER ERROR:", errormessage)
      console.trace()
      this.server.errormsg = errormessage
    },
    updateRules: function(election_rules, whenDone, parameter) {
      this.election_rules = election_rules
      console.log("In updateRules in Main")
      this.createdSettings = true
      if (this.doneCreating()) this.recalculate(whenDone, parameter)
    },
    updateSimulationSettings: function(settings) {
      console.log("updateSimulationSettings in Main")
      this.sim_settings = settings
      //this.sim_settings = Object.assign({}, settings); // shallow copy.
      console.log("In Main, gen_method =", this.sim_settings.gen_method)
    },
    updateVoteTable: function(table) {
      console.log("Updating vote table")
      this.vote_table = table
      this.vote_sums.row = table.votes.map(y => y.reduce((a, b) => a+b))
      this.vote_sums.col = table.votes.reduce((a, b) => a.map((v,i) => v+b[i]))
      this.vote_sums.tot = this.vote_sums.row.reduce((a, b) => a + b, 0)
      this.vote_sums.cseats = 0
      this.vote_sums.aseats = 0
      var c = table.constituencies
      for (var i=0; i<c.length; i++) {
        this.vote_sums.cseats += c[i].num_const_seats
        this.vote_sums.aseats += c[i].num_adj_seats
      }
      this.vote_table_constituencies = c
      this.createdVotes = true;
      if (this.doneCreating()) this.recalculate()
    },
    // Thanks to Pétur Helgi Einarsson for the next two functions
    parse_headers: function (headers) {
      // Return type and name for download file
      var content_type = headers["content-type"];
      var content_disposition = headers["content-disposition"];
      let parts = content_disposition.split(";");
      let download_name = "Example.xlsx"
      for (var i_part in parts) {
        let part = parts[i_part];
        let filename_pos = part.indexOf("filename=");
        if (filename_pos != -1) {
          filename_pos += "filename=".length;
          download_name = part.substring(filename_pos);
        }
      }
      return [content_type, download_name]
    },
    downloadFile: function (promise) {
      console.log("In download file")
      console.log(promise)
      promise.then (
        (response) => {
          const status = response.status;
          if (status != 200) {
            console.log("Server error", response.body.error)
            this.serverError(response.body.error)
          }
          else {
            console.log("Inside status==200")
            console.log("response=", response)
            console.log("headers=", response.headers)
            console.log("content-type", response.headers["content-type"])
            if (response.headers["content-type"] == "application/json") {
              let s,x
              s = String.fromCharCode.apply(null, new Uint8Array(response.data))
              eval("x = " + s)
              if ("error" in x) {
                // API returned error instead of actual blob
                this.serverError(x["error"])
                return
              }
            }
            console.log("data=", response.data)
            let link = document.createElement("a");
            const [type, downloadname] = this.parse_headers(response.headers);
            const blob = new Blob([response.data], {type: type});
            const blobUrl = URL.createObjectURL(blob);
            link.href = blobUrl;
            link.download = downloadname;
            document.body.appendChild(link);
            // Dispatch click event on the link (this is necessary
            // as link.click() does not work in the latest Firefox
            link.dispatchEvent(
              new MouseEvent("click", {
                bubbles: true,
                cancelable: true,
                view: window,
              })
            );
            link.remove();
          }
        },
        (response) => {
          console.log("Error:", response);
        }
      );
    },
    recalculate: function(whenDone, parameter) {
      console.log("this=",this)
      console.log("this.$options=",this.$options)
      console.log("this.$options.name=",this.$options.name)
      this.waitingForData = true
      if (this.election_rules.length > 0) {
        this.$http.post(
          '/api/election/',
          {
            vote_table: this.vote_table,
            rules: this.election_rules,
          }).then(response => {
            if (response.body.error) {
              console.log("error-return 1")
              this.serverError(response.body.error)
            } else {
              this.results = response.body;
              for (var i=0; i<response.body.length; i++){
                this.election_rules.splice(i, 1, response.body[i].rules)
              }
              if (whenDone) whenDone(this.election_rules, parameter)
            }
            this.$nextTick(()=>{this.waitingForData = false})
          }, response => {
            this.serverError("Error in recalculate function")
            this.$nextTick(()=>{this.waitingForData = false})
          });
      }
    },
  },
  Created: function() {
    console.log("Main created")
  }
}
</script>
