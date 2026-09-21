<template>
<div v-if="results.length > 0">
  <h3>Results based on the source votes</h3>
  <DownloadNameDialog
    id="election-results-download-name"
    ref="downloadNameDialog"
    @confirm="saveResults"
  />
  <b-container style="margin-left:0px; margin-bottom:20px">
    <b-button
      class="mb-10"
      style="margin-left:0px"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Download results to local Excel xlsx-file"
      @click="openDownload">
      Download Excel file
    </b-button>
  </b-container>
  <b-tabs v-model="resultIndex" no-key-nav card>
    <b-tab v-for="(system, activeTabIndex) in systems" :key="resultTabKey(system)"
           :title="system.name">
      <template v-if = "results[activeTabIndex] == null">
        <b-alert :show="true">
          No solution exists.
        </b-alert>
      </template>
      <template v-else>
        <b-container fluid align-h="start" v-if="results[activeTabIndex] !== undefined">
          <b-row>
            <h4>Seat allocation</h4>
          </b-row>
            <ResultMatrix
              :constituencies="systems[activeTabIndex].constituencies"
              :parties="vote_table.parties"
              :values="results[activeTabIndex].display_results"
              :party_votes_name="vote_table.party_vote_info.name"
              :party_votes_specified="vote_table.party_vote_info.specified"
              >
            </ResultMatrix>
          <p v-if="results[activeTabIndex].switching_affected">
            * Affected by switching, see table below.
          </p>
          <b-alert :show="!!results[activeTabIndex].ties?.length" variant="warning">
            <strong>Tied allocation scores</strong>
            <p>The first tied entry in table order was selected. An official draw
              of lots could give a different result.</p>
            <ul class="mb-0">
              <li v-for="(tie, index) in results[activeTabIndex].ties" :key="index">
                {{tie.stage}}: {{tie.candidates.join('; ')}}.
                Selected: {{tie.selected}}.
              </li>
            </ul>
          </b-alert>
          <b-row>
            <br>
            <h4>Seat allocation step-by-step</h4>
          </b-row>          
          <b-row>
            <b-col
              v-for="(table, demoIndex) in results[activeTabIndex].demo_tables"
              :key="demoIndex"
              auto
              class="result-demo-column">
              <ResultDemonstration
                :table="table">
              </ResultDemonstration>
            </b-col>
          </b-row>
        </b-container>
      </template>
    </b-tab>
    <template #empty>
      There are no electoral systems specified.
    </template>
  </b-tabs>
</div>
<div  v-else-if="results.length == 0">
  <div v-if="usesPartyVotes() && !partyVotesValid()">
    <b-alert :show="true">
      <h4 class="alert-heading">Election results cannot be calculated.</h4>
      All votes in National party votes and seats must be numbers if they are to be used to compute the total number of seats for each party
    </b-alert>
  </div>
</div>
</template>

<script>
import ResultMatrix from './components/ResultMatrix.vue'
import ResultDemonstration from './components/ResultDemonstration.vue'
import DownloadNameDialog from './components/DownloadNameDialog.vue'
import { timestampedDownloadBasename } from './downloadName.js'
import { mapState, mapActions } from 'vuex';

export default {
  computed: {
    ...mapState([
      'results',
      'vote_table',
      'systems',
      'display_settings',
    ]),
  },
  data: function() {
    return {
      resultIndex: 0,
    }
  },
  components: {
    ResultMatrix,
    ResultDemonstration,
    DownloadNameDialog,
  },
  
  methods: {
    ...mapActions([
      "downloadFile"
    ]),    
    openDownload() {
      const basename = timestampedDownloadBasename('Election')
      this.$refs.downloadNameDialog.open(basename, 'xlsx')
    },
    resultTabKey(system) {
      return [
        system.name,
        system.primary_divider,
        system.adj_determine_divider,
        system.adjustment_preparation_method,
        system.adjustment_method,
        system.adj_alloc_divider,
      ].join('|')
    },
    saveResults: function(destination) {
      let promise = axios({
        method: "post",
        url: "api/election/save/",
        data: {
          vote_table:     this.vote_table,
          systems:        this.systems,
          display_settings: this.display_settings,
        },
        responseType: "arraybuffer",
      });
      this.downloadFile({promise, ...destination})
    },
    usesPartyVotes: function() {
      return this.vote_table.party_vote_info.specified
        && ['party_vote_info', 'average'].includes(this.vote_table.party_vote_basis)
    },
    partyVotesValid: function() {
      return this.vote_table.party_vote_info.votes.every(function(element) {return typeof element == 'number';})
    },
  },
  created: function() {
    console.log("Created Election")
  }
}
</script>
