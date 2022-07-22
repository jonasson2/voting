<template>
<div>
  <b-form style="margin-left:16px">

    <!-- CONSTITUENCY SEAT ALLOCATION -->
    <b-row>
      <legend style="margin-left:0px; margin-top:12px" class="text-center">
        Allocation of constituency seats and national fixed seats
      </legend>
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
            v-model="systems[systemidx].primary_divider"
            :options="capabilities.systems"
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
              v-model.number="systems[systemidx].constituency_threshold"/>
          </b-input-group>
        </b-form-group>
      </b-col>
    </b-row>

    <!-- APPORTIONMENT -->
    <b-row>
      <legend style="margin-left:0px; margin-top:12px" class="text-center">
        Apportionment of adjustment seats to parties
      </legend>
      <b-col cols="5">
        <b-form-group
          label="Rule"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Basic rule used to apportion adjustment seats between parties
                 based on total votes for all lists of the same party."
          >
          <b-form-select
            v-model="systems[systemidx].adj_determine_divider"
            :options="capabilities.systems"/>
        </b-form-group>
      </b-col>
      <b-col cols="7">
        <b-form-group
          label="Threshold"
          label-for="input-horizontal"
          label-cols="auto"
          >
          <b-row>
            <b-col cols="4">
              <b-input-group
                append="%"
                v-b-tooltip.hover.bottom.v-primary.ds500
                title="Threshold as percentage of total votes required by a party
                       to qualify for apportionment of adjustment seats. Choose 0 if
                       not applicable"
                >
                <b-form-input
                  type="number"
                  min="0" max="100"
                  v-model.number="systems[systemidx].adjustment_threshold"/>
              </b-input-group>
            </b-col>
            <b-col cols="3">
              <b-form-group
                label=""
                v-b-tooltip.hover.bottom.v-primary.ds500
                label-for="input-horizontal"
                label-cols="auto"
                title="Choose if one or both thresholds apply"
                >
                <b-form-select
                  v-model="systems[systemidx].adj_threshold_choice"
                  :options="capabilities.adj_threshold_choice"/>
              </b-form-group>
            </b-col>
            <b-col cols="5">
              <b-form-group
                label=""
                v-b-tooltip.hover.bottom.v-primary.ds500
                label-for="input-horizontal"
                label-cols="auto"
                title="Threshold as number of constituency seats required by a party
                       to qualify for apportionment of adjustment seats. Choose 0 if
                       not applicable."
                >
                <b-input-group append="Cons. seats">
                  <b-form-input
                    type="number"
                    min="0" max="10"
                    v-model.number="systems[systemidx].adjustment_threshold_seats"/>
                </b-input-group>
              </b-form-group>
            </b-col>
          </b-row>
        </b-form-group>
      </b-col>
    </b-row>

    <!-- ADJUSTMENT SEAT ALLOCATION -->
    <b-row>
      <legend style="margin-left:0px; margin-top:12px" class="text-center">
        Allocation of adjustment seats to lists</legend>
      <b-col cols="5">
        <b-form-group
          label="Rule"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Rule to allocate adjustment seats to individual party lists within
                 the constituencies."
          >
          <b-form-select
            v-model="systems[systemidx].adj_alloc_divider"
            :options="capabilities.divider_rules"/>
        </b-form-group>
      </b-col>
      <b-col cols="7">
        <b-form-group
          label="Allocation method"
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Method to allocate adjustment seats to party
                 lists based on the given basic rule."
          >
          <b-form-select
            v-model="systems[systemidx].adjustment_method"
            :options="capabilities.adjustment_methods"/>
        </b-form-group>
      </b-col>
    </b-row>

    <!-- CONSTITUENCY AND ADJUSTMENT SEAT NUMBERS -->
    <b-row>
      <legend style="margin-left:0px; margin-top:12px" class="text-center">
        Specification of constituency and adjustment seat numbers
      </legend>
      <b-col cols="6">
        <b-form-group
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Numbers of constituency and adjustment seats in each
                 constituency in this particular electoral system"
          >
          <b-form-select
            v-model="const_spec_option"
            :options="capabilities.seat_spec_options.const"/>
        </b-form-group>
      </b-col>
      <b-col cols="6" v-if='const_spec_option!="refer"'>
        <table v-if="!adding_system && !waiting_for_data" class="votematrix">
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
          <tr v-for="constituency in systems[systemidx].constituencies">
            <th class="displayleft">
              {{ constituency['name'] }}
            </th>
            <td class="displayright">
              <span v-if="const_spec_option != 'custom'">
                {{ constituency['num_const_seats'] }}
              </span>
              <span
                v-if="const_spec_option == 'custom'"
                class="numerical"
                >
                <input
                  type="text"
                  v-autowidth="{minWidth:'50px', maxWidth:'75px'}"
                  v-model.number="constituency['num_const_seats']"f
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
                  v-model.number="constituency['num_adj_seats']">
              </span>
            </td>
          </tr>
        </table>
      </b-col>
    </b-row>

    <!-- PARTY SEAT NUMBERS -->
    <b-row>
      <legend style="margin-left:px; margin-top:12px" class="text-center">
        Specification of party seat numbers
      </legend>
      <b-col cols="6">
        <b-form-group
          v-b-tooltip.hover.bottom.v-primary.ds500
          label-for="input-horizontal"
          label-cols="auto"
          title="Total number of seats for each party in this particular
                 electoral system"
          >
          <b-form-select
            v-model="party_spec_option"
            :options="capabilities.seat_spec_options.party"/>
        </b-form-group>
      </b-col>
    </b-row>
  </b-form>
</div>
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
    party_spec_option: {
      get() { return this.systems[this.systemidx].seat_spec_options.party },
      set(val) {
        this.setPartySpecOption({"opt": val, "idx": this.systemidx})
        this.recalc_sys_const()
      }
    },
  },
  methods: {
    ...mapMutations([
      "setWaitingForData",
      "clearWaitingForData",
      "setConstSpecOption",
      "setPartySpecOption",
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
