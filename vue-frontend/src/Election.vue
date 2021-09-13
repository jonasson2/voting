<template>
<div>
  <b-container style="margin-left:0px; margin-bottom:20px">
    <b-button
      class="mb-10"
      style="margin-left:0px"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Download results to local Excel xlsx-file.
             You may need to change browser settings; see Help for details"
      @click="get_xlsx">
      Download XLSX file
    </b-button>
  </b-container>
  <b-tabs v-model="resultIndex" card>
    <b-tab v-for="(rules, activeTabIndex) in election_rules" :key="activeTabIndex">
      <div slot="title">
        {{rules.name}}
      </div>
      <b-container fluid
                   v-if="results[activeTabIndex] !== undefined">
        <b-row>
          <h3>Seat allocation, constituency and adjustment seats combined</h3>
          <ResultMatrix
            :parties="vote_table.parties"
            :constituencies="results[activeTabIndex].rules.constituencies"
            :values="results[activeTabIndex].seat_allocations"
            :stddev="false">
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
          <h3>Allocation of adjustment seats step-by-step</h3>
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

export default {
  props: {
    "server": { default: {} },
    "vote_table": { default: {} },
    "election_rules": { default: [{}] },
  },
  data: function() {
    return {
      resultIndex: 0,
      results: [],
    }
  },
  components: {
    ResultMatrix,
    ResultChart,
    ResultDemonstration,
  },
  
  watch: {
    'vote_table': {
      handler: function (val, oldVal) {
        console.log("watching vote_table");
        this.recalculate();
      },
      deep: true
    },
    'election_rules': {
      handler: function (val, oldVal) {
        console.log("watching election_rules");
        this.recalculate();
      },
      deep: true
    },
  },
  methods: {
    recalculate: function() {
      console.log("recalculate called");
      if (this.election_rules.length > 0) {
        // && this.election_rules.length > this.activeTabIndex
        // && this.election_rules[this.activeTabIndex].name) {
        this.server.waitingForData = true;
        this.$http.post(
          '/api/election/',
          {
            vote_table: this.vote_table,
            rules: this.election_rules,
          }).then(response => {
            if (response.body.error) {
              this.server.errormsg = response.body.error;
              this.server.waitingForData = false;
            } else {
              this.server.errormsg = '';
              this.server.error = false;
              this.results = response.body;
              console.log("results", this.results);
              for (var i=0; i<response.body.length; i++){
                let old_const = this.election_rules[i].constituencies;
                let new_const = response.body[i].rules.constituencies;
                let modified = false;
                if (new_const.length == old_const.length) {
                  for (var j=0; j<new_const.length; j++) {
                    let old_c = old_const[j];
                    let new_c = new_const[j];
                    if (old_c.name != new_c.name
                        || old_c.num_const_seats != new_c.num_const_seats
                        || old_c.num_adj_seats != new_c.num_adj_seats) {
                      modified = true;
                    }
                  }
                }
                else if (new_const.length>0) {
                  modified = true;
                }
                if (modified){
                  this.$emit('update-rules', response.body[i].rules, i);
                }
              }
              this.server.waitingForData = false;
            }
          }, response => {
            this.server.error = true;
            this.server.waitingForData = false;
          });
      }
    },
    
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
