<template>
<div>
  <b-navbar toggleable="md" type="dark" variant="info">
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <b-alert
    :show="server_error != ''"
    dismissible
    @dismissed="clearServerError()"
    variant="danger"
    >
    Server error: {{server_error}}
  </b-alert>
  <b-tabs
    active-nav-item-class="font-weight-bold"
    card
    >
    <b-tab title="Votes and seats" active @click="showDataTabs()">
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        @download-file="downloadFile"
        >
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems" @click="showDataTabs()">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems
        @download-file="downloadFile"
        >
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election" @click="calculate_results()">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->      
      <Election
        @download-file="downloadFile"
        >
      </Election>
    </b-tab>
    <b-tab title="Simulated elections" @click="showSimulate()">
      <!-- <P>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate
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
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
  components: {
    VoteMatrix,
    Election,
    Simulate,
    ElectoralSystems,
    Intro,
  },
  
  computed: mapState(['server_error']),
  
  methods: {
    ...mapMutations([
      "clearServerError",
      "showDataTabs",
      "showSimulate",
    ]),
    ...mapActions([
      "calculate_results"
    ]),
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
  },
  created: function() {
    console.log("Main created")
  }
}
</script>
