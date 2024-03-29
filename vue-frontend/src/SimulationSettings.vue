<template>
<!-- <b-form style = "margin-left:16px;margin-right:16px"> -->
  <b-form style="margin-left:16px;margin-right:16px" v-if="!waiting_for_data">
    <b-row>
      <b-col cols=4>
        <b-form-group
          label="Number of simulations"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="How many vote tables should be generated?
                 (How many simulations should be run?)"
          >
          <b-form-input
            type="number"
            v-model.number="sim_settings.simulation_count"
            min="0"/>
        </b-form-group>
        <b-form-group
          label="Number of cpus"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          :title="max_cpu_count_text"
          >
          <b-form-select
            v-model="sim_settings.cpu_count"
            :options="sim_capabilities.cpu_counts"
            />
        </b-form-group>
        <b-form-group
          label="Generating distribution"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="Distribution used to simulate votes of each list, with the
                 specified coefficient of variation and the source votes as 
                 expected values"
          >
          <b-form-select
            v-model="sim_settings.gen_method"
            :options="sim_capabilities.generating_methods"
            />
        </b-form-group>
        <b-form-group
          label="Coefficient of variation for constituency votes"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="Standard deviation of simulated votes divided by their mean.
                 Valid range 0–0.75 (beta), 0–1 (gamma), 0–0.577 (uniform)."
          >
          <b-input-group>
            <b-form-input
              type="text"
              v-model.number="sim_settings.const_cov"/>
          </b-input-group>
        </b-form-group>
        <b-form-group
          label="Coefficient of variation for national party votes"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="Standard deviation of simulated votes divided by their mean.
                 Valid range 0–0.75 (beta), 0–1 (gamma), 0–0.577 (uniform)."
          >
          <b-input-group>
            <b-form-input
              type="text"
              v-model.number="sim_settings.party_vote_cov"/>
          </b-input-group>
        </b-form-group>
        <b-form-group
          label="Simulate with thresholds?"
          v-b-tooltip.hover.bottom.v-primary.ds500
          style="font-size:110%"
          label-for="input-horizontal"
          label-cols="auto"
          title="Choose if thresholds apply"
          >
          <b-form-select
            v-model="sim_settings.use_thresholds"
            :options="sim_capabilities.use_thresholds"/>
        </b-form-group>
        <!-- <b-form-group -->
        <!--   label="Apply randomness to" -->
        <!--   style="font-size:110%" -->
        <!--   v-b-tooltip.hover.bottom.v-primary.ds500 -->
        <!--   label-for="input-horizontal" -->
        <!--   label-cols="auto" -->
        <!--   title="Only the specified constituency will have its votes drawn  -->
        <!--          at random, the remaining constituencies will use the  -->
        <!--          reference votes on all replications. Default is to draw  -->
        <!--          all votes at random." -->
        <!--   > -->
        <!--   <b-input-group> -->
        <!--     <b-form-select -->
        <!--       v-model="sim_settings.selected_rand_constit" -->
        <!--       :options="const_names" -->
        <!--       /> -->
        <!--   </b-input-group> -->
        <!-- </b-form-group> -->
      </b-col>
      <b-col cols=4>
        <b-form-group style="font-size:110%"
                      description='Scaled seat shares are used as reference in quality 
                                   measurements; "Help" for more details'>
          <label> <b>Scaling of votes for reference seat shares:</b> </label>
          <b-form-radio-group
            id="A"
            v-model="sim_settings.scaling"
            >
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each constituency and each party (scale both rows and columns of vote table)"
              value="both"
              >
              {{scaling_name("both")}}
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each constituency (scale rows of vote table)"
              value="const"
              >          
              {{scaling_name("const")}}
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each party (scale columns of vote table)"
              value="party"
              >
              {{scaling_name("party")}}
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats
                     nationally (scales all entries in vote table by the same factor)"
              value="total"
              >
              {{scaling_name("total")}}
            </b-form-radio>
          </b-form-radio-group>
        </b-form-group>
      </b-col>
      <b-col cols=4>
        <b-form-group style="font-size:110%">
          <label><b>Electoral systems used for comparison:</b></label>
          <b-form-checkbox-group
            v-model = "comparison_systems"
            :options = "system_names"
            stacked
            >
          </b-form-checkbox-group>
        </b-form-group>
      </b-col>
    </b-row>
  </b-form>
</template>

<script>
import { mapState, mapMutations } from 'vuex';

export default {
  computed: {
    ...mapState([
      'sim_settings',
      'sim_capabilities',
      'systems',
      'waiting_for_data'
    ]),
    system_names: function() {
      let sysnames = this.systems.map(system => system.name)
      console.log("NAMES=", sysnames)
      console.log("comparison_systems=", this.comparison_systems)
      return sysnames
    },
    max_cpu_count_text: function() {
      let text = "How many cpus (cores) should be used? (out of a maximum of "
        + Math.max(...this.sim_capabilities.cpu_counts) + ")"
      return text
    },
    const_names: function() {
      console.log("this.systems=", this.systems)
      let cnames = this.systems[0].constituencies.map(con => con.name)
      cnames.unshift("All constituencies")
      return cnames
    }
  },
  data: function () {
    return {
      created: false,
      comparison_systems: [],
      selected: '',
    }
  },
  methods: {
    // The following function should maybe be moved to startsimulation
    // to force listening to beforeunload if simulation has been run
    //...mapMutations(["setSimulateCreated"])
    scaling_name: function(scaling) {
      return this.sim_capabilities.scaling_names[scaling]
    },
  },
  watch: {
    comparison_systems: {
      handler: function (val) {
        console.log("this.created", this.created)
        if (this.created) {
          console.log("val", val)
          this.$store.commit("updateComparisonSystems", val)
        }
      },
      deep: true
    },
  },
  created: function() {
    this.comparison_systems = this.systems.flatMap(
      sys => sys.compare_with ? [sys.name] : [])
    this.created = true
  },
}
</script>
