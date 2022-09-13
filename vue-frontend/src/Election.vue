<template>
<div v-if="results.length > 0">
  <h3>Results based on the source votes</h3>
  <b-container style="margin-left:0px; margin-bottom:20px">
    <b-button
      class="mb-10"
      style="margin-left:0px"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Download results to local Excel xlsx-file"
      @click="saveResults">
      Download Excel file
    </b-button>
  </b-container>
  <b-tabs v-model="resultIndex" no-key-nav card>
    <b-tab v-for="(system, activeTabIndex) in systems" :key="activeTabIndex">
      <div slot="title">
        {{system.name}}
      </div>
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
              :voteless="results[activeTabIndex].voteless_seats"
              :party_votes_name="vote_table.party_vote_info.name"
              :party_votes_specified="vote_table.party_vote_info.specified"
              >
            </ResultMatrix>
          <!-- <b-row> -->
            <!--   <ResultChart -->
            <!--     :parties="vote_table.parties" -->
            <!--     :seats="results[activeTabIndex].seat_allocations"> -->
              <!--   </ResultChart> -->
            <!-- </b-row> -->
          <b-row>
            <br>
            <h4>Allocation of adjustment seats step-by-step</h4>
          </b-row>          
          <b-row>
            <b-col auto>
              <ResultDemonstration
                :table="results[activeTabIndex].demo_tables[0]">
              </ResultDemonstration>
            </b-col>
            <b-col auto v-if="results[activeTabIndex].demo_tables.length > 1">
              <ResultDemonstration
                :table="results[activeTabIndex].demo_tables[1]">
              </ResultDemonstration>
            </b-col>
          </b-row>
        </b-container>
      </template>
    </b-tab>
    <div slot="empty">
      There are no electoral systems specified.
    </div>
  </b-tabs>
</div>
<div  v-else-if="results.length == 0">
  <div v-if="showAlert()==false && showAlert1()">
    <b-alert :show="true">
      <h4 class="alert-heading">Election results cannot be calculated.</h4>
      The total number of seats for each party cannot be computed using national party votes when they are not specified
    </b-alert>
  </div>
  <div v-else-if="showAlert() && showAlert1() && showAlert2()==false">
    <b-alert :show="true">
      <h4 class="alert-heading">Election results cannot be calculated.</h4>
      All votes in National party votes and seats must be numbers if they are to be used to compute the total number of seats for each party
    </b-alert>
  </div>
</div>
</template>

<script>
import ResultMatrix from './components/ResultMatrix.vue'
import ResultChart from './components/ResultChart.vue'
import ResultDemonstration from './components/ResultDemonstration.vue'
import { mapState, mapActions } from 'vuex';

export default {
  computed: {
    ...mapState([
      'results',
      'vote_table',
      'systems',
    ]),
  },
  data: function() {
    return {
      resultIndex: 0,
    }
  },
  components: {
    ResultMatrix,
    ResultChart,
    ResultDemonstration,
  },
  
  methods: {
    ...mapActions([
      "downloadFile"
    ]),    
    saveResults: function() {
      let promise = axios({
        method: "post",
        url: "/api/election/save",
        data: {
          vote_table:     this.vote_table,
          systems:        this.systems,
        },
        responseType: "arraybuffer",
      });
      this.downloadFile(promise)
    },
    showAlert: function() {
      return this.vote_table.party_vote_info.specified
    },
    showAlert1: function() {
      let seat_spec_options = this.systems.map(({seat_spec_options}) => seat_spec_options)
      let party = seat_spec_options.map(({party}) => party)
      return ['party_vote_info', 'average'].some(element => party.includes(element))
    },
    showAlert2: function() {
      return this.vote_table.party_vote_info.votes.every(function(element) {return typeof element == 'number';})
    },
  },
  created: function() {
    console.log("Created Election")
  }
}
</script>
