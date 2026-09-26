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
            v-autowidth="{ maxWidth: '175px', minWidth: '88px' }"
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
          title="Optional integer seed for repeatable generated votes and random tie decisions. Use - for fresh random draws.">
          <label for="simulation-random-seed">Random seed</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-random-seed" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '175px', minWidth: '88px' }"
              v-model.number="randomSeedInput"
              @focus="$event.target.select()"
              @blur="restoreRandomSeed"/>
          </span>
        </div>
        <hr class="simulation-settings-divider">
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Distribution used to vary list support before each
                 constituency is rescaled to its source vote total.">
          <label for="simulation-distribution">Generating distribution</label>
          <b-form-select id="simulation-distribution"
            class="compact-select simulation-distribution-select simulation-setting-control"
            v-model="sim_settings.gen_method"
            :options="sim_capabilities.generating_methods"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Relative standard deviation of list-vote draws before each
                 constituency is rescaled to its source vote total.
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
          title="Correlation used to generate list-vote draws within each
                 party before constituency totals are rescaled. Use only
                 with lognormal distribution; otherwise 0 is used.">
          <label for="simulation-const-corr">Correlation between list votes within each party</label>
          <span class="simulation-setting-control compact-entry">
            <input id="simulation-const-corr" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.const_corr"/>
          </span>
        </div>
        <div v-if="vote_table.party_vote_info.specified" class="simulation-setting-row"
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
        <div v-if="vote_table.party_vote_info.specified" class="simulation-setting-row"
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
        <hr class="simulation-settings-divider">
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Selecting No disables all thresholds and other party-qualification rules, except &quot;Stand in all constituencies&quot;.">
          <label for="simulation-thresholds">Simulate with thresholds?</label>
          <b-form-select id="simulation-thresholds"
            class="compact-select simulation-threshold-select simulation-setting-control"
            v-model="sim_settings.use_thresholds"
            :options="sim_capabilities.use_thresholds"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Compare the product of allocated-seat quotients with the largest achievable product under the selected rule and constraints. 100% is optimal.">
          <label for="simulation-entropy-score">Calculate entropy score?</label>
          <b-form-select id="simulation-entropy-score"
            class="compact-select simulation-threshold-select simulation-setting-control"
            v-model="sim_settings.entropy_score"
            :options="sim_capabilities.use_thresholds"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="For every simulated election, perturb its votes at several small CoVs and measure how many seats move between parties and between lists within parties.">
          <label for="simulation-sensitivity">Compute sensitivity measures?</label>
          <b-form-select id="simulation-sensitivity"
            class="compact-select simulation-threshold-select simulation-setting-control"
            v-model="sim_settings.sensitivity"
            :options="sim_capabilities.use_thresholds"/>
        </div>
        <template v-if="sim_settings.sensitivity">
          <div class="simulation-setting-row"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Number of minor vote perturbations generated at every sensitivity CoV for each simulated election.">
            <label for="sensitivity-simulation-count">Number of perturbations per major simulation</label>
            <span class="simulation-setting-control compact-entry">
              <input id="sensitivity-simulation-count" class="compact-entry-input"
                type="text"
                v-autowidth="{ maxWidth: '122px', minWidth: '62px' }"
                v-model.number="sim_settings.sensitivity_simulation_count"/>
            </span>
          </div>
          <div class="simulation-setting-row"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Distribution used for independent multiplicative perturbations around each simulated vote table.">
            <label for="sensitivity-distribution">Sensitivity generating distribution</label>
            <b-form-select id="sensitivity-distribution"
              class="compact-select simulation-distribution-select simulation-setting-control"
              v-model="sim_settings.sensitivity_gen_method"
              :options="sim_capabilities.generating_methods"/>
          </div>
          <div class="simulation-setting-row sensitivity-cov-row"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Positive, distinct CoVs at which sensitivity is calculated, in increasing order.">
            <label>Sensitivity CoVs</label>
            <span class="simulation-setting-control sensitivity-cov-list">
              <span class="sensitivity-cov-item"
                v-for="(cov, index) in sim_settings.sensitivity_covs"
                :key="index">
                <span class="compact-entry">
                  <input class="compact-entry-input" type="text"
                    v-autowidth="{ maxWidth: '70px', minWidth: '35px' }"
                    v-model.number="sim_settings.sensitivity_covs[index]"
                    :aria-label="`Sensitivity CoV ${index + 1}`"/>
                  <span class="compact-entry-unit">%</span>
                </span>
                <b-button v-if="index === sim_settings.sensitivity_covs.length - 1"
                  variant="link" size="sm" class="sensitivity-cov-remove"
                  :disabled="sim_settings.sensitivity_covs.length === 1"
                  v-b-tooltip.hover.bottom.v-primary.ds500
                  title="Remove sensitivity CoV"
                  @click="removeSensitivityCov(index)">X</b-button>
              </span>
              <b-button size="sm" class="sensitivity-cov-add"
                v-b-tooltip.hover.bottom.v-primary.ds500
                title="Add sensitivity CoV"
                @click="addSensitivityCov">
                <span class="add-button-symbol">+</span>
              </b-button>
            </span>
          </div>
        </template>
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
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500="{ customClass: 'scaling-tooltip' }"
              title="Fractional reference seat shares satisfy both important margins: each constituency's seat total and each party's nationally proportional entitlement.">
              <b-form-radio value="both">{{scaling_name("both")}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each constituency (scale rows of vote table)">
              <b-form-radio value="const">{{scaling_name("const")}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each party (scale columns of vote table)">
              <b-form-radio value="party">{{scaling_name("party")}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats
                     nationally (scales all entries in vote table by the same factor)">
              <b-form-radio value="total">{{scaling_name("total")}}</b-form-radio>
            </div>
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
      'vote_table',
      'systems',
      'waiting_for_data'
    ]),
    randomSeedInput: {
      get() {
        return this.sim_settings.random_seed == null ? '-' : this.sim_settings.random_seed
      },
      set(value) {
        this.sim_settings.random_seed = value
      },
    },
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
    addSensitivityCov() {
      const covs = this.sim_settings.sensitivity_covs
      const last = Number(covs[covs.length - 1])
      const previous = Number(covs[covs.length - 2])
      const increment = covs.length > 1 && last > previous ? last - previous : 1
      covs.push((Number.isFinite(last) ? last : 0) + increment)
    },
    removeSensitivityCov(index) {
      if (this.sim_settings.sensitivity_covs.length > 1) {
        this.sim_settings.sensitivity_covs.splice(index, 1)
      }
    },
    restoreRandomSeed() {
      const seed = this.sim_settings.random_seed
      if (typeof seed === 'string' && seed.trim() === '') {
        this.sim_settings.random_seed = '-'
      }
    },
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

<style scoped>
.scaling-option {
  width: fit-content;
  max-width: 100%;
}

.simulation-settings-divider {
  border: 0;
  border-top: 2px solid #000;
  margin: 0.5em 0;
}

.sensitivity-cov-list,
.sensitivity-cov-item {
  align-items: center;
  display: inline-flex;
}

.sensitivity-cov-list {
  flex-wrap: wrap;
  gap: 5px;
}

.sensitivity-cov-remove {
  font-weight: 400;
  line-height: 1;
  margin-left: 4px;
  padding: 2px 3px;
}

.sensitivity-cov-add {
  padding: 2px 7px;
}
</style>
