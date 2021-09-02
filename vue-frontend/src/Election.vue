<template>
<div>
  <h2>Results</h2>
  <b-card no-body>
    <b-tabs v-model="resultIndex" card>
      <b-tab v-for="(rules, idx) in election_rules" :key="idx">
        <div slot="title">
          {{rules.name}}
        </div>
        <b-container style="margin-left:1px; margin-bottom:10px">
          <b-button @click="get_xlsx">Download XLSX file</b-button>
        </b-container>
        <b-container fluid style="margin-top:5px" v-if="results[idx] !== undefined">
          <b-row>
            <ResultMatrix
              :parties="vote_table.parties"
              :constituencies="results[idx].rules.constituencies"
              :values="results[idx].seat_allocations"
              :stddev="false">
            </ResultMatrix>
          </b-row>
          <!-- <b-row> -->
          <!--   <ResultChart -->
          <!--     :parties="vote_table.parties" -->
          <!--     :seats="results[idx].seat_allocations"> -->
          <!--   </ResultChart> -->
          <!-- </b-row> -->
          <b-row>
            <ResultDemonstration
              :table="results[idx].step_by_step_demonstration">
            </ResultDemonstration>
          </b-row>
        </b-container>
      </b-tab>
      <div slot="empty">
        There are no electoral systems specified.
      </div>
    </b-tabs>
  </b-card>

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
