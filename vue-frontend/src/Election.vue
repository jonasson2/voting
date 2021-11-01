<template>
<div v-if="!waiting_for_data && results.length > 0">
  <h3>Results based on values in Votes and seats tab</h3>
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
  <b-tabs v-model="resultIndex" card>
    <b-tab v-for="(rules, activeTabIndex) in systems" :key="activeTabIndex">
      <div slot="title">
        {{rules.name}}
      </div>
      <b-container fluid
                   v-if="results[activeTabIndex] !== undefined">
        <b-row>
          <h4>Seat allocation, constituency and adjustment seats combined</h4>
          <ResultMatrix
            :constituencies="sys_constituencies[activeTabIndex]"
            :parties="vote_table.parties"
            :values="results[activeTabIndex].seat_allocations"
            :stddev="false"
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
import { mapState } from 'vuex';

export default {
  computed: mapState([
    'results',
    'vote_table',
    'systems',
    'sys_constituencies',
    'waiting_for_data'
  ]),
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
    
    saveResults: function() {
      let promise = axios({
        method: "post",
        url: "/api/election/save",
        data: {
          vote_table:     this.vote_table,
          rules:          this.systems,
          constituencies: this.sys_constituencies
        },
        responseType: "arraybuffer",
      });
      this.$emit("download-file", promise);
    }
  },
  created: function() {
    console.log("Created Election")
  }
}
</script>
