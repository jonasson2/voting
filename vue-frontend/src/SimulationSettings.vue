<template>
<!-- <b-form style = "margin-left:16px;margin-right:16px"> -->
  <b-form style = "margin-left:16px;margin-right:16px">   
    <b-row>
      <b-col cols="3">
        <b-form-group
          label="Number of simulations"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input"
          title="How many simulations should be run?
                 Select 0 to use only reference data instead of any simulated data."
          >
          <b-form-input
            type="number"
            v-model.number="settings.simulation_count"
            min="0"/>
        </b-form-group>
      </b-col>
      <b-col cols="3">
        <b-form-group
          label="Generating method"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input"
          title="Method used to generate random votes
                 (based on the supplied vote table)."
          >
          <b-form-select
            v-model="settings.gen_method"
            :options="capabilities.generating_methods"
            class="mb-3"/>
        </b-form-group>
      </b-col>
      <b-col cols="3">
        <b-form-group
          label="Coefficient of variation"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input"
          title="This is the standard deviation of simulated votes
                 divided by their mean. Valid range 0–0.75 (beta), 0–0.577 (uniform)."
          >
          <b-input-group>
            <b-form-input
              type="text"
              v-model.number="settings.distribution_parameter"/>
          </b-input-group>
        </b-form-group>
      </b-col>
      <b-col cols="3">
        <b-form-group
          label="Apply randomness to"
          style="font-size:110%"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input"
          title="Only the specified constituency will have its votes drawn 
                 at random, the remaining constituencies will use the 
                 reference votes on all replications. Default is to draw 
                 all votes at random."
          >
          <b-input-group>
            <b-form-select
              v-model="settings.selected_rand_constit"
              :options="rand_constit"
              />
          </b-input-group>
        </b-form-group>
      </b-col>
    </b-row>
    <b-form-group
      label='Scaling of reference seat shares'
      style="font-size:110%"
      description='Scaled seat shares are used as reference in quality 
                   measurements; "Help" for more details'
      >
      <b-form-radio-group
        id="A"
        v-model="settings.scaling"
        >
        <b-form-radio
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Adjust the vote shares so that they sum to the total number of seats for
                 each constituency and each party (scale both rows and columns of vote table)"
          value="both"
          >
          by both constituency and party seats
        </b-form-radio><br>
        <b-form-radio
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Adjust the vote shares so that they sum to the total number of seats for
                 each constituency (scale rows of vote table)"
          value="const"
          >
          by constituency seats
        </b-form-radio><br>
        <b-form-radio
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Adjust the vote shares so that they sum to the total number of seats for
                 each party (scale columns of vote table)"
          value="party"
          >by party seats
        </b-form-radio><br>
        <b-form-radio
          v-b-tooltip.hover.bottom.v-primary.ds500
          title="Adjust the vote shares so that they sum to the total number of seats
                 nationally (scales all entries in vote table by the same factor)"
          value="total"
          >
          by total seats
        </b-form-radio>
      </b-form-radio-group>
    </b-form-group>
  </b-form>
</template>

<script>
export default {
  props: [
    "constituencies",
    "sim_settings"
  ],
  data: function () {
    return {
      settings: this.sim_settings,
      capabilities: {},
      selected: '',
      rand_constit: [],
      doneCreating: false,
      watching: true,
    }
  },
  methods: {
    make_rand_constit: function(constituencies) {
      this.rand_constit = ["All"]
      for (var con in constituencies) {
        this.rand_constit.push(constituencies[con].name)
      }
    },
  },
  watch: {
    sim_settings: {
      handler: function(val) {
        if (this.watching && this.doneCreating) this.settings = val
      },
      deep: true
    },
    constituencies: {
      handler: function (val, oldVal) {
        this.make_rand_constit(val)
      },
      deep: true
    },
    settings: {
      handler: function (val, oldVal) {
        if (this.doneCreating) {
          this.watching = false
          this.$emit('update-sim-settings', val);
          this.$nextTick(()=>{this.watching = true})
        }
      },
      deep: true
    },
  },
  created: function() {
    if (!this.doneCreating) {
      this.$http.post('/api/capabilities', {}).then(response => {
        this.capabilities = response.body.capabilities;
        this.settings = response.body.sim_settings
        this.$emit('update-sim-settings', response.body.sim_settings);
        this.make_rand_constit(this.constituencies);
        this.doneCreating = true;
        console.log("Created SimulationSettings")
      }, response => {
        this.serverError = true;
      });
    }
  },
}
</script>
