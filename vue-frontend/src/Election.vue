<template>
<div>
  <h2>Results</h2>
  <b-container style="margin-left:1px; margin-bottom:10px">
    <b-button size="lg" @click="get_xlsx">Download XLSX file</b-button>
  </b-container>
  <b-container fluid style="margin-top:5px" v-if="results[activeTabIndex] !== undefined">
    <b-row>
      <ResultMatrix
        :parties="vote_table.parties"
        :constituencies="results[activeTabIndex].rules.constituencies"
        :values="results[activeTabIndex].seat_allocations"
        :stddev="false">
      </ResultMatrix>
    </b-row>
    <b-row>
      <ResultChart
        :parties="vote_table.parties"
        :seats="results[activeTabIndex].seat_allocations">
      </ResultChart>
    </b-row>
    <b-row>
      <ResultDemonstration
        :table="results[activeTabIndex].step_by_step_demonstration">
      </ResultDemonstration>
    </b-row>
  </b-container>

</div>
</template>

<script>
import ResultMatrix from './components/ResultMatrix.vue'
import ResultChart from './components/ResultChart.vue'
import ResultDemonstration from './components/ResultDemonstration.vue'

export default {
  props: {
    "server": { default: {} },
    "vote_table": { default: {} },
    "results": {default: [] },
    "election_rules": { default: [{}] },
    "activeTabIndex": { default: 0 },
  },
  components: {
    ResultMatrix,
    ResultChart,
    ResultDemonstration,
  },

  methods: {
    get_xlsx: function() {
      this.$http.post('/api/election/getxlsx/', {
        vote_table: this.vote_table,
        rules: this.election_rules,
      }).then(response => {
        let link = document.createElement('a')
        link.href = '/api/downloads/get?id=' + response.data.download_id
        link.click()
      }, response => {
        this.server.error = true;
      })
    }
  },
}
</script>
