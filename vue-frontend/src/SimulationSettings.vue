<template>
<!-- <b-form style = "margin-left:16px;margin-right:16px"> -->
  <b-form style = "margin-left:16px;margin-right:16px">
    <b-row>
      <b-col cols=4>
        <b-form-group
          label="Number of simulations"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="How many simulations should be run?
                 Select 0 to use only reference data instead of any simulated data."
          >
          <b-form-input
            type="number"
            v-model.number="sim_settings.simulation_count"
            min="0"/>
        </b-form-group>
        <b-form-group
          label="Generating method"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          >
          <b-form-select
            v-model="sim_settings.gen_method"
            :options="capabilities.generating_methods"
            />
        </b-form-group>
        <b-form-group
          label="Coefficient of variation"
          label-cols="auto"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          title="This is the standard deviation of simulated votes
                 divided by their mean. Valid range 0–0.75 (beta), 0–0.577 (uniform)."
          >
          <b-input-group>
            <b-form-input
              type="text"
              v-model.number="sim_settings.distribution_parameter"/>
          </b-input-group>
        </b-form-group>
        <b-form-group
          label="Apply randomness to"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Only the specified constituency will have its votes drawn 
                 at random, the remaining constituencies will use the 
                 reference votes on all replications. Default is to draw 
                 all votes at random."
          >
          <b-input-group>
            <b-form-select
              v-model="sim_settings.selected_rand_constit"
              :options="const_names"
              />
          </b-input-group>
        </b-form-group>
      </b-col>
      <b-col cols=4>
        <b-form-group style="font-size:110%"
                      description='Scaled seat shares are used as reference in quality 
                                   measurements; "Help" for more details'>
          <label> <b>Scaling of reference seat shares:</b> </label>
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
              within both constituencies and parties
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each constituency (scale rows of vote table)"
              value="const"
              >          
              within constituencies
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats for
                     each party (scale columns of vote table)"
              value="party"
              >
              within parties
            </b-form-radio><br>
            <b-form-radio
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjust the vote shares so that they sum to the total number of seats
                     nationally (scales all entries in vote table by the same factor)"
              value="total"
              >
              nationally
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
import { mapState } from 'vuex';

export default {
  computed: {
    ...mapState([
      'sim_settings',
      'systems',
      'sys_constituencies'
    ]),
    system_names: function() {
      let sysnames = this.systems.map(system => system.name)
      console.log("NAMES=", sysnames)
      console.log("comparison_systems=", this.comparison_systems)
      return sysnames
    },
    const_names: function() {
      console.log("this.systems=", this.systems)
      let cnames = this.sys_constituencies.map(syscon => syscon.name)
      cnames.unshift("All constituencies")
      return cnames
    }
  },
  data: function () {
    return {
      created: false,
      comparison_systems: [],
      capabilities: {},
      selected: '',
    }
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
    this.$http.post('/api/capabilities', {}).then(response => {
      this.capabilities = response.body.capabilities;
      this.$store.commit("updateSimSettings", response.body.sim_settings)
      console.log("Created SimulationSettings")
      this.created = true
    }, response => {
      this.serverError = true;
    });
  },
}
</script>
