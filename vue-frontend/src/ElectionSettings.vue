<template>
<div>
  <b-form style="margin-left:16px">
    <b-row>
      <legend style = "margin-left:0px">
        Allocation of constituency seats
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
            v-model="system.primary_divider"
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
              v-model.number="system.constituency_threshold"/>
          </b-input-group>
        </b-form-group>
      </b-col>
    </b-row>
    <b-row>
      <legend style = "margin-left:0px">
        Apportionment of adjustment seats to parties
      </legend>
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
            v-model="system.adj_determine_divider"
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
              v-model.number="system.adjustment_threshold"/>
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
            v-model="system.adj_alloc_divider"
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
            v-model="system.adjustment_method"
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
            v-model="system.seat_spec_option"
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
          <tr v-for="(constituency, conidx) in system.constituencies">
            <th class="displayleft">
              {{ constituency['name'] }}
            </th>
            <td class="displayright">
              <span v-if="system.seat_spec_option != 'custom'">
                {{ constituency['num_const_seats'] }}
              </span>
              <span v-if="system.seat_spec_option == 'custom'">
                <input type="text"
                       v-model.number="constituency['num_const_seats']">
              </span>
            </td>
            <td class="displayright">
              <span v-if="system.seat_spec_option != 'custom'">
                {{ constituency['num_adj_seats'] }}
              </span>
              <span v-if="system.seat_spec_option == 'custom'">
                <input type="text"
                       v-model.number="constituency['num_adj_seats']">
              </span>
            </td>
          </tr>
        </table>
      </b-col>
    </b-row>
  </b-form>
</div>
</template>

<script>
export default {
  props: [
    "newSystem",
    "systemidx",
    "vote_table_constituencies",
    "vote_table"
  ],
  data: function () {
    return {
      system: {},
      capabilities: [{}],
      watching: false,
    }
  },
  methods: {
    getNewSystem: function(newSystem) {
      this.system = newSystem
      this.$nextTick(()=>{this.watching = true})
    },
  },
  watch: {
    system: {
      handler: function (val) {
        if (this.watching) {
          console.log("Watching system in ElectionSettins, system = ", val)
          this.watching = false
          this.$emit('update-system', val, this.systemidx, this.getNewSystem)
        }
      },
      deep: true
    }
  },
  
  created: function() {
    console.log("Creating ElectionSettings")
    console.log("idx=", this.systemidx, ", newSystem=", this.newSystem)
    console.log("system=", this.system)
    var isNew = "name" in this.newSystem
    console.log("isNew: ", isNew)
    this.$http.post(
      '/api/capabilities',
      this.vote_table_constituencies,
    ).then(response => {
      let r = response.body
      this.capabilities = r.capabilities;
      if (!("name" in this.newSystem)) {
        this.system = r.election_rules;
        console.log("Emitting from created in ElectionSettings")
        this.$emit('update-system', r.election_rules, this.systemidx)
        //this.$emit('update-sim-settings', r.sim_settings)
      }
      else {
        this.system = this.newSystem
        console.log("updated system=", this.system)
      }
      this.$nextTick(()=>{this.watching = true})
    }, response => {
      this.$emit("server-error", "server error in Election settings")
      this.$nextTick(()=>{this.watching = true})
    })
  }
}
</script>
