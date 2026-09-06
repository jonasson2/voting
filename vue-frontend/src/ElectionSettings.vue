<template>
<b-form>
  <!-- FIXED SEAT ALLOCATION -->
  <legend class="settings-heading"
    v-b-tooltip.hover.bottom.v-primary.ds500
    title="Information on how to allocate fixed seats to lists in each constituency, and national fixed seats if present">
    Allocation of fixed seats
  </legend>
  <div class="settings-row">
    <label class="settings-field"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Formula used for allocating fixed seats to party lists within each constituency, and national fixed seats to parties if present.">
      <span>Rule</span>
      <b-form-select class="compact-select settings-rule"
        v-model="systems[systemidx].primary_divider"
        :options="capabilities.systems"/>
    </label>
    <label class="settings-field settings-fixed-threshold"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Threshold as percentage of valid votes in a constituency required by a list to qualify for fixed seats in that constituency, also applies to national fixed seats.">
      <span>Threshold</span>
      <span class="compact-entry">
        <input class="compact-entry-input" type="text"
          v-autowidth="{ maxWidth: '70px', minWidth: '25px' }"
          v-model.number="systems[systemidx].constituency_threshold"/>
        <span class="compact-entry-unit">%</span>
      </span>
    </label>
  </div>

  <!-- APPORTIONMENT -->
  <legend class="settings-heading"
    v-b-tooltip.hover.bottom.v-primary.ds500
    title="Information on how to calculate the total number of seats which each party receives">
    Apportionment of total seats to parties
  </legend>
  <div class="settings-row">
    <label class="settings-field"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Formula used to apportion adjustment seats between parties based on chosen votes.">
      <span>Rule</span>
      <b-form-select class="compact-select settings-rule"
        v-model="systems[systemidx].adj_determine_divider"
        :options="capabilities.systems"/>
    </label>
  </div>
  <div class="settings-row">
    <label class="settings-field"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Threshold as percentage of total votes required by a party to qualify for apportionment of adjustment seats. Choose 0 if not applicable">
      <span>Threshold</span>
      <span class="compact-entry">
        <input class="compact-entry-input" type="text"
          v-autowidth="{ maxWidth: '70px', minWidth: '25px' }"
          v-model.number="systems[systemidx].adjustment_threshold"/>
        <span class="compact-entry-unit">%</span>
      </span>
    </label>
    <b-form-select class="compact-select settings-threshold-choice"
      aria-label="Threshold combination"
      v-model="systems[systemidx].adj_threshold_choice"
      :options="capabilities.adj_threshold_choice"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Choose if one or both thresholds apply"/>
    <label class="compact-entry"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Threshold as number of fixed seats required by a party to qualify for apportionment of adjustment seats. Choose 0 if not applicable.">
      <input class="compact-entry-input" type="text"
        v-autowidth="{ maxWidth: '70px', minWidth: '25px' }"
        v-model.number="systems[systemidx].adjustment_threshold_seats"/>
      <span class="compact-entry-unit fixed-seats-unit">fixed seats</span>
    </label>
  </div>

  <!-- ADJUSTMENT SEAT ALLOCATION -->
  <legend class="settings-heading"
    v-b-tooltip.hover.bottom.v-primary.ds500
    title="Information on how to allocate adjustment seats to individual lists in each constituency">
    Allocation of adjustment seats to lists
  </legend>
  <div class="settings-row">
    <label class="settings-field"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Method to allocate adjustment seats to party lists based on the rule chosen below.">
      <span>Allocation method</span>
      <b-form-select class="compact-select settings-method"
        v-model="systems[systemidx].adjustment_method"
        @change="threshold_method(systemidx)"
        :options="capabilities.adjustment_methods"/>
    </label>
  </div>
  <div class="settings-row">
    <label class="settings-field"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Formula used to allocate adjustment seats to individual party lists.">
      <span>Rule</span>
      <b-form-select class="compact-select settings-rule"
        v-model="systems[systemidx].adj_alloc_divider"
        :options="capabilities.divider_rules"/>
    </label>
  </div>
  <!-- FIXED AND ADJUSTMENT SEAT NUMBERS -->
  <legend class="settings-heading">
    Alternative specification of fixed and adjustment seat numbers
  </legend>
  <div class="settings-row">
    <b-form-select class="compact-select settings-seat-spec"
      aria-label="Fixed and adjustment seat numbers"
      v-b-tooltip.hover.bottom.v-primary.ds500
      title="Numbers of fixed and adjustment seats in this electoral system"
      v-model="const_spec_option"
      :options="capabilities.seat_spec_options.const"/>
    <div v-if='const_spec_option!="refer"' class="settings-seat-table">
      <table v-if="!adding_system && !waiting_for_data" class="votematrix">
        <tbody>
        <tr>
          <th class="topleft"></th>
          <th class="displaycenter"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Fixed seats">
            # Fixed
          </th>
          <th class="displaycenter"
              v-b-tooltip.hover.bottom.v-primary.ds500
              title="Adjustment seats">
            # Adj.
          </th>
        </tr>
        <tr v-for="constituency in systems[systemidx].constituencies">
          <th class="displayleft">
            {{ constituency['name'] }}
          </th>
          <td class="displayright">
            <span v-if="const_spec_option != 'custom'">
              {{ constituency['num_fixed_seats'] }}
            </span>
            <span
              v-if="const_spec_option == 'custom'"
              class="numerical"
              >
              <input
                type="text"
                v-autowidth="{minWidth:'50px', maxWidth:'75px'}"
                v-model.number="constituency['num_fixed_seats']"
                >
            </span>
          </td>
          <td class="displayright">
            <span v-if="const_spec_option != 'custom'">
              {{ constituency['num_adj_seats'] }}
            </span>
            <span
              v-if="const_spec_option == 'custom'"
              class="numerical"
              >
              <input
                type="text"
                v-autowidth="{minWidth:'50px', maxWidth:'75px'}"
                v-model.number="constituency['num_adj_seats']"
                >
            </span>
          </td>
        </tr>
        <tr v-if="vote_table.party_vote_info.specified">
          <th class="displayleft">
            {{ vote_table.party_vote_info['name'] }}
          </th>
          <td class="displayright">
            <span v-if="const_spec_option != 'custom'">
              {{ systems[systemidx].nat_seats.num_fixed_seats }}
            </span>
            <span
              v-if="const_spec_option == 'custom'"
              class="numerical"
              >
              <input
                type="text"
                v-autowidth="{minWidth:'50px', maxWidth:'75px'}"
                v-model.number="systems[systemidx].nat_seats.num_fixed_seats"
                >
            </span>
          </td>
          <td class="displayright">
            <span v-if="const_spec_option != 'custom'">
              {{ systems[systemidx].nat_seats.num_adj_seats }}
            </span>
            <span
              v-if="const_spec_option == 'custom'"
              class="numerical"
              >
              <input
                type="text"
                v-autowidth="{minWidth:'50px', maxWidth:'75px'}"
                v-model.number="systems[systemidx].nat_seats.num_adj_seats"
                >
            </span>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</b-form>
</template>

<script>
import { mapState, mapMutations, mapActions } from 'vuex';
export default {
  data: function() {
    return {
      created: false
    }
  },
  computed: {
    ...mapState([
      'vote_table',
      'systems',
      'waiting_for_data',
    ]),
    const_spec_option: {
      get() { return this.systems[this.systemidx].seat_spec_options.const },
      set(val) {
        this.setConstSpecOption({"opt": val, "idx": this.systemidx})
        this.recalc_sys_const()
      }
    },
  },
  methods: {
    ...mapMutations([
      "setWaitingForData",
      "clearWaitingForData",
      "setConstSpecOption",
      "threshold_method",
    ]),
    ...mapActions([
      'recalc_sys_const',
    ]),
  },
  props: [
    "systemidx",
    "capabilities",
    "adding_system"
  ],
  created: function() {
    console.log("Creating ElectionSettings")
    console.log(this.capabilities.systems)
    console.log("vote_table", this.vote_table)
  }
}
</script>

<!-- ORDER OF ALLOCATION -->
<!-- Allocate to constituency lists first -->
<!-- Allocate interchangeably to constituency lists and national list -->
<!-- Allocate to national list first -->
