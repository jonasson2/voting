<template>
<!-- <b-form style = "margin-left:16px;margin-right:16px"> -->
  <b-form style="margin-left:16px;margin-right:16px" v-if="!waiting_for_data">
    <b-row class="simulation-settings-layout">
      <b-col class="simulation-settings-column simulation-settings-inputs">
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="How many vote tables should be generated?
                 (How many simulations should be run?)">
          <label for="simulation-count">Number of simulations</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-count" class="compact-entry-input" type="text"
            v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
            v-model.number="sim_settings.simulation_count"
            min="0"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          :title="max_cpu_count_text">
          <label for="simulation-cpu-count">Number of cpus</label>
          <b-form-select id="simulation-cpu-count"
            class="compact-select simulation-cpu-select simulation-setting-control"
            v-model="sim_settings.cpu_count"
            :options="sim_capabilities.cpu_counts"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Distribution used to simulate votes of each list, with the
                 specified relative SD and the source votes as 
                 expected values">
          <label for="simulation-distribution">Generating distribution</label>
          <b-form-select id="simulation-distribution"
            class="compact-select simulation-distribution-select simulation-setting-control"
            v-model="sim_settings.gen_method"
            :options="sim_capabilities.generating_methods"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Standard deviation of simulated votes divided by their mean.
                 Valid range 0-1 (lognormal), 0–0.75 (beta), 0–1 (gamma),
                 0–0.577 (uniform).">
          <label for="simulation-const-rsd">Relative standard deviation for list votes</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-const-rsd" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.const_rsd"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Correlation between list votes within each party,
                 use only with lognormal distribution, else 0 is used.">
          <label for="simulation-const-corr">Correlation between list votes within each party</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-const-corr" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.const_corr"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Standard deviation of simulated votes divided by their mean.
                 Valid range 0-1 (lognormal), 0–0.75 (beta), 0–1 (gamma),
                 0–0.577 (uniform).">
          <label for="simulation-party-rsd">Relative standard deviation for national party votes</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-party-rsd" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.party_vote_rsd"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Correlation between list votes and national party votes,
                 use only with lognormal distribution, else 0 is used.">
          <label for="simulation-party-corr">Correlation between list votes and national party votes</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-party-corr" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.party_vote_corr"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Choose if thresholds apply">
          <label for="simulation-thresholds">Simulate with thresholds?</label>
          <b-form-select id="simulation-thresholds"
            class="compact-select simulation-threshold-select simulation-setting-control"
            v-model="sim_settings.use_thresholds"
            :options="sim_capabilities.use_thresholds"/>
        </div>
      </b-col>
      <b-col class="simulation-settings-scaling">
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
      <b-col class="simulation-settings-comparison">
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
