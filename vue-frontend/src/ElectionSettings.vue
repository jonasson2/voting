<template>
<b-form style="margin-left:16px">
  <b-row>
    <legend style = "margin-left:0px">Allocation of constituency seats</legend>
    <b-col cols="7">
      <b-form-group
        label="Rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Basic rule used for allocating constituency seats to 
               party lists within each constituency."
        >
        <b-form-select
          v-model="rules.primary_divider"
          :options="capabilities.rules"
          />
      </b-form-group>
    </b-col>
    <b-col cols="5">
      <b-form-group
        label="Threshold"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Threshold as percentage of valid votes in a constituency 
               required by a list to qualify for seats in that constituency."
        >
        <b-input-group append="%">
          <b-form-input
            type="number" min="0" max="100"
            v-model.number="rules.constituency_threshold"/>
        </b-input-group>
      </b-form-group>
    </b-col>
  </b-row>
  <b-row>
    <legend style = "margin-left:0px">Apportionment of adjustment seats to parties</legend>
    <b-col cols="7">
      <b-form-group
        label="Rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Basic rule used to apportion adjustment seats betwwen parties 
               based on total votes for all lists of the same party."
        >
        <b-form-select
          v-model="rules.adj_determine_divider"
          :options="capabilities.rules"/>
      </b-form-group>
    </b-col>
    <b-col cols="5">
      <b-form-group
        label="Threshold"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Threshold as percentage of total votes required by a party 
               to qualify for apportionment of adjustment seats."
        >
        <b-input-group append="%">
          <b-form-input
            type="number"
            min="0" max="100"
            v-model.number="rules.adjustment_threshold"/>
        </b-input-group>
      </b-form-group>
    </b-col>
  </b-row>
  <b-row>
    <legend style = "margin-left:0px">Allocation of adjustment seats to lists</legend>
    <b-col cols="5">
      <b-form-group
        label="Basic rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Rule to allocate adjustment seats to individual party lists within 
               the constituencies."
        >
        <b-form-select
          v-model="rules.adj_alloc_divider"
          :options="capabilities.divider_rules"/>
      </b-form-group>
    </b-col>
    <b-col cols="7">
      <b-form-group
        label="Allocation method"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Method to allocate adjustment seats to party lists based on the given basic rule."
        >
        <b-form-select
          v-model="rules.adjustment_method"
          :options="capabilities.adjustment_methods"/>
      </b-form-group>
    </b-col>
  </b-row>
  <b-row>
    <b-col cols="6">
      <legend style="margin-left:-16px">Specification of seat numbers</legend>
      <b-form-group
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Numbers of constituency and adjustment seats in each constituency in this particular electoral system"
        >
        <b-form-select
          v-model="rules.seat_spec_option"
          :options="capabilities.seat_spec_options"/>
      </b-form-group>
    </b-col>
    <b-col cols="6">
      <table class="votematrix">
        <tr>
          <th class="topleft"></th>
          <th class="displaycenter"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Constituency seats">
            # Cons.
          </th>
          <th class="displaycenter"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjustment seats">
            # Adj.
          </th>
        </tr>
        <tr v-for="(constituency, conidx) in constituencies">
          <th class="displayleft">
            {{ constituency['name'] }}
          </th>
          <td class="displayright">
            <span v-if="rules.seat_spec_option != 'custom'">
              {{ constituency['num_const_seats'] }}
            </span>
            <span v-if="rules.seat_spec_option == 'custom'">
              <input type="text"
                     v-model.number="constituency['num_const_seats']">
            </span>
          </td>
          <td class="displayright">
            <span v-if="rules.seat_spec_option != 'custom'">
              {{ constituency['num_adj_seats'] }}
            </span>
            <span v-if="rules.seat_spec_option == 'custom'">
              <input type="text"
                     v-model.number="constituency['num_adj_seats']">
            </span>
          </td>
        </tr>
      </table>
    </b-col>
  </b-row>
</b-form>
</template>

<script>
export default {
  props: [
    "rulesidx",
    "single_rules",
    "constituencies"
  ],
  data: function () {
    return {
      doneCreating: false,
      capabilities: {},
      rules: this.single_rules
    }
  },
  watch: {
    'rules': {
      handler: function (val, oldVal) {
        if (this.doneCreating) {
          console.log("watching rules");
          this.$emit('update-single-rules', val, this.rulesidx);
        }
      },
      deep: true
    }
  },
  created: function() {
    console.log("constituencies:", this.constituencies)
    this.$http.post(
      '/api/capabilities',
      this.constituencies,
    ).then(response => {
      this.capabilities = response.body.capabilities;      
      console.log("Created ElectionSettings");
      console.log("constituencies:", this.constituencies)
      console.log("constituencies:", response.body.election_rules.constituencies)
      this.rules = response.body.election_rules;
      this.$emit('update-single-rules', response.body.election_rules, this.rulesidx);
      //this.$emit('update-simulation-rules', response.body.simulation_rules)
      this.doneCreating = true;
    }, response => {
      this.serverError = true;
    })
  }
}
</script>
