<template>
  <b-form style="margin-left:16px;margin-right:16px" v-if="!waiting_for_data">
    <b-row class="simulation-settings-layout">
      <b-col class="simulation-settings-column simulation-settings-inputs">
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="How many vote tables should be generated?
                 (How many simulations should be run?)">
          <label for="simulation-count">Number of simulations</label>
          <span class="compact-entry">
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
            class="compact-select simulation-cpu-select"
            v-model="sim_settings.cpu_count"
            :options="sim_capabilities.cpu_counts"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Optional integer seed for repeatable generated votes and random tie decisions. Use - for fresh random draws.">
          <label for="simulation-random-seed">Random seed</label>
          <span class="compact-entry">
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
          <span class="compact-entry simulation-distribution-control">
            <b-form-select id="simulation-distribution"
              class="compact-select simulation-distribution-select"
              v-model="sim_settings.gen_method"
              :options="sim_capabilities.generating_methods"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Relative standard deviation (coefficient of variation; CoV)
                 of list-vote draws before each constituency is rescaled to its source vote total.
                 Valid range 0-1 (lognormal), 0–0.75 (beta), 0–1 (gamma),
                 0–0.577 (uniform).">
          <label for="simulation-const-rsd">Relative standard deviation for list votes</label>
          <span class="compact-entry">
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
          <span class="compact-entry">
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
          <span class="compact-entry">
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
          <span class="compact-entry">
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
            class="compact-select simulation-threshold-select"
            v-model="sim_settings.use_thresholds"
            :options="sim_capabilities.use_thresholds"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Compare the product of allocated-seat quotients with the largest achievable product under the selected rule and constraints. 100% is optimal.">
          <label for="simulation-entropy-score">Calculate entropy score?</label>
          <b-form-select id="simulation-entropy-score"
            class="compact-select simulation-threshold-select"
            v-model="sim_settings.entropy_score"
            :options="sim_capabilities.use_thresholds"/>
        </div>
      </b-col>
      <b-col class="simulation-settings-scaling">
        <b-form-group style="font-size:110%">
          <label v-b-tooltip.hover.bottom.v-primary.ds500
            title='Scaled seat shares are used as reference in quality measurements; "Help" for more details'>
            <b>Scaling of votes for reference seat shares</b>
          </label>
          <b-form-radio-group
            id="A"
            v-model="sim_settings.scaling"
            >
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500="{ customClass: 'scaling-tooltip' }"
              title="Fractional reference seat shares satisfy both important margins: each constituency's seat total and each party's nationally proportional entitlement.">
              <b-form-radio value="both">{{sim_capabilities.scaling_names.both}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each constituency (scale rows of vote table)">
              <b-form-radio value="const">{{sim_capabilities.scaling_names.const}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each party (scale columns of vote table)">
              <b-form-radio value="party">{{sim_capabilities.scaling_names.party}}</b-form-radio>
            </div>
            <div class="scaling-option"
              v-b-tooltip.hover.top.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats
                     nationally (scales all entries in vote table by the same factor)">
              <b-form-radio value="total">{{sim_capabilities.scaling_names.total}}</b-form-radio>
            </div>
          </b-form-radio-group>
        </b-form-group>
      </b-col>
      <b-col class="simulation-settings-sensitivity">
        <div class="simulation-settings-section-title">Sensitivity analysis</div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="For every simulated election, perturb its votes at several small CoVs and measure how many seats move between parties and between lists within parties.">
          <label for="simulation-sensitivity">Compute sensitivity measures?</label>
          <b-form-select id="simulation-sensitivity"
            class="compact-select simulation-threshold-select"
            v-model="sim_settings.sensitivity"
            :options="sim_capabilities.use_thresholds"/>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Number of minor vote perturbations generated at every sensitivity CoV for each simulated election.">
          <label for="sensitivity-simulation-count">Perturbations per simulation</label>
          <span class="compact-entry">
            <input id="sensitivity-simulation-count" class="compact-entry-input"
              type="text"
              v-autowidth="{ maxWidth: '122px', minWidth: '62px' }"
              v-model.number="sim_settings.sensitivity_simulation_count"/>
          </span>
        </div>
        <div class="simulation-setting-row"
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Distribution used for independent multiplicative perturbations around each simulated vote table.">
          <label for="sensitivity-distribution">Generating distribution</label>
          <span class="compact-entry simulation-distribution-control">
            <b-form-select id="sensitivity-distribution"
              class="compact-select simulation-distribution-select"
              v-model="sim_settings.sensitivity_gen_method"
              :options="sim_capabilities.generating_methods"/>
          </span>
        </div>
        <div class="sensitivity-cov-section">
          <div class="sensitivity-cov-label"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="CoV means coefficient of variation (relative standard deviation).
                   Enter distinct positive values; they sort when you leave a cell.">
            Perturbation CoVs
          </div>
          <table class="votematrix sensitivity-cov-table" aria-label="Perturbation CoVs">
            <tbody>
              <tr v-for="(cov, index) in sim_settings.sensitivity_covs" :key="index">
                <td class="sensitivity-cov-action">
                  <b-button variant="link" size="sm" class="xbutton"
                    :disabled="sim_settings.sensitivity_covs.length === 1"
                    :aria-label="`Remove perturbation CoV ${index + 1}`"
                    @click="removeSensitivityCov(index)">X</b-button>
                </td>
                <td class="sensitivity-cov-value">
                  <input :id="`sensitivity-cov-${index}`" type="text"
                    v-autowidth="{ maxWidth: '70px', minWidth: '35px' }"
                    v-model.number="sim_settings.sensitivity_covs[index]"
                    @blur="sortSensitivityCovs"
                    :aria-label="`Perturbation CoV ${index + 1}`"/>%
                </td>
              </tr>
              <tr>
                <th class="growtable sensitivity-cov-action">
                  <b-button size="sm" aria-label="Add perturbation CoV"
                    v-b-tooltip.hover.bottom.v-primary.ds500
                    title="Add perturbation CoV"
                    @click="addSensitivityCov"><span class="add-button-symbol">+</span></b-button>
                </th>
              </tr>
            </tbody>
          </table>
        </div>
      </b-col>
    </b-row>
  </b-form>
</template>

<script>
import { mapState } from 'vuex';

export default {
  computed: {
    ...mapState([
      'sim_settings',
      'sim_capabilities',
      'vote_table',
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
    max_cpu_count_text() {
      return `How many cpus (cores) should be used? (out of a maximum of ${Math.max(...this.sim_capabilities.cpu_counts)})`
    }
  },
  methods: {
    sortSensitivityCovs() {
      const covs = this.sim_settings.sensitivity_covs
      const values = covs.map(Number)
      if (values.some(value => !Number.isFinite(value) || value <= 0)
          || new Set(values).size !== values.length) return
      covs.splice(0, covs.length, ...values.sort((left, right) => left - right))
    },
    addSensitivityCov() {
      const covs = this.sim_settings.sensitivity_covs
      const last = Number(covs[covs.length - 1])
      const previous = Number(covs[covs.length - 2])
      const [mantissa, exponent = '0'] = String(last).split('e')
      const decimalDigits = (mantissa.split('.')[1] || '').length
      const firstStep = Number.isFinite(last) && last > 0
        ? 10 ** Math.min(0, Number(exponent) - decimalDigits) : 1
      const increment = covs.length > 1 && last > previous
        ? last - previous : firstStep
      const valid = covs.map(Number).filter(Number.isFinite)
      const highest = valid.length ? Math.max(...valid) : 0
      const next = highest + increment
      const rounded = Number(next.toPrecision(15))
      covs.push(rounded > highest ? rounded : next)
      this.sortSensitivityCovs()
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

.simulation-settings-section-title {
  font-size: 110%;
  font-weight: bold;
  margin-bottom: 9px;
}

.sensitivity-cov-section {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.sensitivity-cov-label {
  padding-top: 3px;
}

.sensitivity-cov-table .sensitivity-cov-action {
  text-align: center;
  width: 36px;
}

.sensitivity-cov-table .sensitivity-cov-action .xbutton {
  padding: 0;
}

.sensitivity-cov-table .sensitivity-cov-value input {
  border: 0;
  outline-offset: 1px;
  text-align: right;
}
</style>
