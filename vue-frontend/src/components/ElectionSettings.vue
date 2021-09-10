<template>
<b-form>
  <br>
  <b-row>
    <legend style = "margin-left:16px">Allocation of constituency seats</legend>
    <b-col cols="7">
      <b-form-group
        label="Rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Basic rule used for allocating constituency seats to party lists within each constituency."
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
        title="Threshold as percentage of valid votes in a constituency required by a list to qualify for seats in that constituency."
        >
        <b-input-group append="%">
          <b-form-input
            type="number" min="0" max="100"
            v-model.number="rules.constituency_threshold"/>
        </b-input-group>
      </b-form-group>
    </b-col>
  </b-row>
  <br>
  <b-row>
    <legend style = "margin-left:16px">Apportionment of adjustment seats to parties</legend>
    <b-col cols="7">
      <b-form-group
        label="Rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Basic rule used to apportion adjustment seats betwwen parties based on total votes for all lists of the same party."
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
        title="Threshold as percentage of total votes required by a party to qualify for apportionment of adjustment seats."
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
  <br>
  <b-row>
    <legend style = "margin-left:16px">Allocation of adjustment seats to lists</legend>
    <b-col cols="5">
      <b-form-group
        label="Basic rule"
        v-b-tooltip.hover.bottom.v-primary.ds500
        label-for="input-horizontal"
        label-cols="auto"
        title="Rule to allocate adjustment seats to individual party lists within the constituencies."
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
  <br>
  <b-row>
    <b-col cols="6">
      <legend>Specification of seat numbers</legend>
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
        <tr class="parties">
          <th class="topleft"></th>
          <th class="seatnumberheading"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Constituency seats">
            # Cons.
          </th>
          <th class="seatnumberheading"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjustment seats">
            # Adj.
          </th>
          <!-- <th> -->
          <!--   <abbr title="Constituency seats"># Cons.</abbr> -->
          <!-- </th> -->
          <!-- <th> -->
          <!--   <abbr title="Adjustment seats"># Adj.</abbr> -->
          <!-- </th> -->
        </tr>
        <tr v-for="(constituency, conidx) in rules.constituencies">
          <th class="constname">
            {{ constituency['name'] }}
          </th>
          <td class="partyvotes">
            <span v-if="rules.seat_spec_option != 'custom'">
              {{ constituency['num_const_seats'] }}
            </span>
            <span v-if="rules.seat_spec_option == 'custom'">
              <input type="text"
                     v-model.number="constituency['num_const_seats']">
            </span>
          </td>
          <td class="partyvotes">
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
    "rules",
  ],
  data: function () {
    return {
      doneCreating: false,
      capabilities: {},
    }
  },
  watch: {
    'rules': {
      handler: function (val, oldVal) {
        if (this.doneCreating) {
          console.log("emitting update-rules from watch rules in ElectionSettings");
          this.$emit('update-rules', val, this.rulesidx);
        }
      },
      deep: true
    }
  },
  created: function() {
    console.log("Created ElectionSettings");
    this.$http.get('/api/capabilities').then(response => {
      this.capabilities = response.body.capabilities;
      if (!("name" in this.rules)){
        this.$emit('update-rules', response.body.election_rules, this.rulesidx);
      }
      this.doneCreating = true;
    }, response => {
      this.serverError = true;
    });
  },
}
</script>
