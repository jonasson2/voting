<template>
  <b-form>
    <b-row>
      <b-col>
        <b-form-group
          label="Name"
          description="Give this electoral system a name."
        >
          <b-form-input type="text" class="mb-3" v-model="rules.name"/>
        </b-form-group>
      </b-col>
    </b-row>
    <b-row>
      <b-col>
        <fieldset>
          <legend>Allocation of constituency seats</legend>
          <b-form-group
            label="Rule"
            description="Basic rule used for allocating constituency seats to party lists within each constituency."
          >
            <b-form-select class="mb-3"
              v-model="rules.primary_divider"
              :options="capabilities.rules"/>
          </b-form-group>
          <b-form-group
            label="Threshold"
            description="Threshold as percentage of valid votes in a constituency required by a list to qualify for seats in that constituency."
          >
            <b-input-group append="%">
              <b-form-input type="number" min="0" max="100"
                v-model.number="rules.constituency_threshold"/>
            </b-input-group>
          </b-form-group>
        </fieldset>
      </b-col>
      <b-col>
        <fieldset>
          <legend>Apportionment of adjustment seats</legend>
          <b-form-group
            label="Rule"
            description="Basic rule used to apportion adjustment seats betwwen parties based on total votes for all lists of the same party."
          >
            <b-form-select class="mb-3"
              v-model="rules.adj_determine_divider"
              :options="capabilities.rules"/>
          </b-form-group>
          <b-form-group
            label="Threshold"
            description="Threshold as percentage of total votes required by a party to qualify for apportionment of adjustment seats."
          >
            <b-input-group append="%">
              <b-form-input type="number" min="0" max="100"
                v-model.number="rules.adjustment_threshold"/>
            </b-input-group>
          </b-form-group>
        </fieldset>
      </b-col>
      <b-col>
        <fieldset>
          <legend>Allocation of adjustment seats to individual lists</legend>
          <b-form-group
            label="Rule"
            description="Basic rule used in the method for allocating adjustment seats to individual lists."
          >
            <b-form-select class="mb-3"
              v-model="rules.adj_alloc_divider"
              :options="capabilities.divider_rules"/>
          </b-form-group>
          <b-form-group
            label="Method"
            description="Which method should be used to allocate adjustment seats?"
          >
            <b-form-select class="mb-3"
              v-model="rules.adjustment_method"
              :options="capabilities.adjustment_methods"/>
          </b-form-group>
        </fieldset>
      </b-col>
    </b-row>
    <b-row>
      <b-col cols="5">
        <b-form-group
          label="Seat specification option"
          description="Which seat distribution should this electoral system use?"
        >
          <b-form-select class="mb-3"
            v-model="rules.seat_spec_option"
            :options="capabilities.seat_spec_options"/>
        </b-form-group>
      </b-col>
      <b-col>
        <table class="votematrix">
          <tr class="parties">
            <th class="topleft"></th>
            <th>
              <abbr title="Constituency seats"># Cons.</abbr>
            </th>
            <th>
              <abbr title="Adjustment seats"># Adj.</abbr>
            </th>
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
