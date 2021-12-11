<template>
<div v-if="results.length > 0">
  <h3>Results based on source Votes and seats</h3>
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
        <b-container fluid v-if="results[activeTabIndex] !== undefined">
          <b-row>
            <h4>Seat allocation</h4>
            <ResultMatrix
              :constituencies="systems[activeTabIndex].constituencies"
              :parties="vote_table.parties"
              :values="results[activeTabIndex].display_results"
              :voteless="results[activeTabIndex].voteless_seats"
              >
            </ResultMatrix>
          </b-row>
          <!-- <b-row> -->
            <!--   <ResultChart -->
            <!--     :parties="vote_table.parties" -->
            <!--     :seats="results[activeTabIndex].seat_allocations"> -->
              <!--   </ResultChart> -->
            <!-- </b-row> -->
          <b-row>
            <br>
            <h4>Allocation of adjustment seats step-by-step</h4>
            <ResultDemonstration
              :table="results[activeTabIndex].step_by_step_demonstration">
            </ResultDemonstration>
          </b-row>
        </b-container>
      </template>
    </b-tab>
    <div slot="empty">
      There are no electoral systems specified.
    </div>
  </b-tabs>
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
    }
  },
  created: function() {
    console.log("Created Election")
  }
}
</script>
