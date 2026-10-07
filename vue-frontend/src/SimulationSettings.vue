<template>
  <b-form style="margin-left:16px;margin-right:16px" v-if="!waiting_for_data">
    <b-row class="simulation-settings-layout">
      <b-col class="simulation-settings-column simulation-settings-inputs">
        <div class="simulation-setting-row">
          <label for="simulation-count"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="How many vote tables should be generated?
                 (How many simulations should be run?)">Number of simulations</label>
          <span class="compact-entry">
            <input id="simulation-count" class="compact-entry-input" type="text"
            v-autowidth="{ maxWidth: '175px', minWidth: '88px' }"
            v-model.number="sim_settings.simulation_count"
            min="0"/>
          </span>
        </div>
        <div class="simulation-setting-row">
          <label for="simulation-cpu-count"
            v-b-tooltip.hover.bottom.v-primary.ds500
            :title="max_cpu_count_text">Number of cpus</label>
          <b-form-select id="simulation-cpu-count"
            class="compact-select simulation-cpu-select"
            v-model="sim_settings.cpu_count"
            :options="sim_capabilities.cpu_counts"/>
        </div>
        <div class="simulation-setting-row">
          <label for="simulation-random-seed"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Optional integer seed for repeatable generated votes and random tie decisions. Use - for fresh random draws.">Random seed</label>
          <span class="compact-entry">
            <input id="simulation-random-seed" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '175px', minWidth: '88px' }"
              v-model.number="randomSeedInput"
              @focus="$event.target.select()"
              @blur="restoreRandomSeed"/>
          </span>
        </div>
        <hr class="simulation-settings-divider">
        <div class="simulation-setting-row">
          <label for="simulation-distribution"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Distribution used to vary list support before each
                 constituency is rescaled to its source vote total.">Generating distribution</label>
          <span class="compact-entry simulation-distribution-control">
            <b-form-select id="simulation-distribution"
              class="compact-select simulation-distribution-select"
              v-model="sim_settings.gen_method"
              :options="sim_capabilities.generating_methods"/>
          </span>
        </div>
        <div class="simulation-setting-row">
          <label for="simulation-const-rsd"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Relative standard deviation (coefficient of variation; CoV)
                 of list-vote draws before each constituency is rescaled to its source vote total.
                 Valid range 0-1 (lognormal), 0–0.75 (beta), 0–1 (gamma),
                 0–0.577 (uniform).">Relative standard deviation for list votes</label>
          <span class="compact-entry">
            <input id="simulation-const-rsd" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.const_rsd"/>
          </span>
        </div>
        <div class="simulation-setting-row">
          <label for="simulation-const-corr"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Correlation used to generate list-vote draws within each
                 party before constituency totals are rescaled. Use only
                 with lognormal distribution; otherwise 0 is used.">Correlation between list votes within each party</label>
          <span class="compact-entry">
            <input id="simulation-const-corr" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.const_corr"/>
          </span>
        </div>
        <div v-if="vote_table.party_vote_info.specified" class="simulation-setting-row">
          <label for="simulation-party-rsd"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Standard deviation of simulated votes divided by their mean.
                 Valid range 0-1 (lognormal), 0–0.75 (beta), 0–1 (gamma),
                 0–0.577 (uniform).">Relative standard deviation for national party votes</label>
          <span class="compact-entry">
            <input id="simulation-party-rsd" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.party_vote_rsd"/>
          </span>
        </div>
        <div v-if="vote_table.party_vote_info.specified" class="simulation-setting-row">
          <label for="simulation-party-corr"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Correlation between list votes and national party votes,
                 use only with lognormal distribution, else 0 is used.">Correlation between list votes and national party votes</label>
          <span class="compact-entry">
            <input id="simulation-party-corr" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '100px', minWidth: '50px' }"
              v-model.number="sim_settings.party_vote_corr"/>
          </span>
        </div>
        <hr class="simulation-settings-divider">
        <div class="simulation-setting-row">
          <b-form-checkbox id="simulation-thresholds" v-model="sim_settings.use_thresholds">
            <span v-b-tooltip.hover.bottom.v-primary.ds500
              title="Unchecking disables all thresholds and other party-qualification rules, except &quot;Stand in all constituencies&quot;.">
              Simulate with thresholds
            </span>
          </b-form-checkbox>
        </div>
        <div class="simulation-setting-row">
          <b-form-checkbox id="simulation-entropy-score" v-model="sim_settings.entropy_score">
            <span v-b-tooltip.hover.bottom.v-primary.ds500
              title="Compare the product of allocated-seat quotients with the largest achievable product under the selected rule and constraints. 100% is optimal.">
              Calculate entropy score
            </span>
          </b-form-checkbox>
        </div>
        <hr class="simulation-settings-divider">
        <h5 class="simulation-settings-section-title">Show additional measures</h5>
        <b-form-checkbox v-model="sim_settings.show_additional">
          Additional proportionality measures
        </b-form-checkbox>
        <b-form-checkbox v-model="sim_settings.show_single_seat">
          Specifically for single-seat constituencies
        </b-form-checkbox>
      </b-col>
      <b-col class="simulation-settings-column simulation-settings-scaling">
        <h5 class="simulation-settings-section-title" v-b-tooltip.hover.bottom.v-primary.ds500
          title='Select the fractional-seat benchmarks to calculate. Adding a benchmark requires a new simulation. The dedicated local indices are always calculated.'>
          Reference scaling
        </h5>
        <b-form-checkbox-group
          id="A"
          v-model="sim_settings.scaling"
          >
          <div class="scaling-option"
            v-b-tooltip.hover.top.v-primary.ds500
            title="Adjust the vote shares so that they sum to the total number of seats for
                   each constituency (scale rows of vote table)">
            <b-form-checkbox value="const">Local scaling</b-form-checkbox>
          </div>
          <div class="scaling-option"
            v-b-tooltip.hover.top.v-primary.ds500="{ customClass: 'scaling-tooltip' }"
            title="Fractional reference seat shares satisfy both important margins: each constituency's seat total and each party's nationally proportional entitlement.">
            <b-form-checkbox value="both">Double scaling</b-form-checkbox>
          </div>
          <div class="scaling-option"
            v-b-tooltip.hover.top.v-primary.ds500
            title="Adjust the vote shares so that they sum to the total number of seats for
                   each party (scale columns of vote table)">
            <b-form-checkbox value="party">Party scaling</b-form-checkbox>
          </div>
          <div class="scaling-option"
            v-b-tooltip.hover.top.v-primary.ds500
            title="Adjust the vote shares so that they sum to the total number of seats
                   nationally (scales all entries in vote table by the same factor)">
            <b-form-checkbox value="total">National scaling</b-form-checkbox>
          </div>
        </b-form-checkbox-group>
      </b-col>
      <b-col class="simulation-settings-column simulation-settings-sensitivity">
        <h5 class="simulation-settings-section-title">Sensitivity analysis</h5>
        <div class="simulation-setting-row">
          <b-form-checkbox id="simulation-sensitivity" v-model="sim_settings.sensitivity">
            <span v-b-tooltip.hover.bottom.v-primary.ds500
              title="For every simulated election, perturb its votes at several small CoVs and measure how many seats move between parties and between lists within parties.">
              Compute sensitivity measures
            </span>
          </b-form-checkbox>
        </div>
        <div class="simulation-setting-row">
          <b-form-checkbox id="single-list-sensitivity" v-model="sim_settings.single_list_sensitivity">
            <span v-b-tooltip.hover.bottom.v-primary.ds500
              title="Choose a party uniformly, then one of its positive-vote constituency lists uniformly. Perturb only that list, without rescaling; use the same draw for every electoral system.">
              Compute single-list sensitivity
            </span>
          </b-form-checkbox>
        </div>
        <div class="simulation-setting-row">
          <label for="sensitivity-simulation-count"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Number of minor vote perturbations generated at every sensitivity CoV for each simulated election.">Perturbations per simulation</label>
          <span class="compact-entry">
            <input id="sensitivity-simulation-count" class="compact-entry-input"
              type="text"
              v-autowidth="{ maxWidth: '122px', minWidth: '62px' }"
              v-model.number="sim_settings.sensitivity_simulation_count"/>
          </span>
        </div>
        <div class="simulation-setting-row">
          <label for="single-list-simulation-count" v-b-tooltip.hover.bottom.v-primary.ds500
            title="Number of single-list perturbations at each CoV for each simulated election. Independent of the ordinary sensitivity perturbation count.">Single-list perturbations per simulation</label>
          <span class="compact-entry">
            <input id="single-list-simulation-count" class="compact-entry-input" type="text"
              v-autowidth="{ maxWidth: '122px', minWidth: '62px' }"
              v-model.number="sim_settings.single_list_simulation_count"/>
          </span>
        </div>
        <div class="simulation-setting-row">
          <label for="sensitivity-distribution"
            v-b-tooltip.hover.bottom.v-primary.ds500
            title="Distribution used for independent multiplicative perturbations around each simulated vote table.">Generating distribution</label>
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
