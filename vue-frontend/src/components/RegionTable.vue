<template>
  <div>
    <legend class="vote-table-section-heading">Regions</legend>
    <div class="table-scroll">
      <table class="votematrix region-table">
        <thead v-if="voteTable.regions && voteTable.regions.length">
          <tr><th>Abbreviation</th><th>Name</th><th># Adj.</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="(region, index) in voteTable.regions" :key="index">
            <td><input type="text" :value="region.abbreviation"
              :aria-label="`Region ${index + 1}: abbreviation`"
              v-autowidth="{minWidth: '40px', maxWidth: '150px'}"
              @change="rename(index, $event)" /></td>
            <td><input type="text" v-model="region.name"
              :aria-label="`Region ${index + 1}: name`"
              v-autowidth="{minWidth: '80px', maxWidth: '350px'}" /></td>
            <td class="numerical"><input type="text" v-model.number="region.num_adj_seats"
              :aria-label="`Region ${region.abbreviation}: adjustment seats`"
              v-autowidth="{minWidth: '25px', maxWidth: '100px'}" /></td>
            <td><b-button variant="link" size="sm" class="xbutton"
              v-b-tooltip.hover.bottom.v-primary.ds500 title="Remove region"
              @click="removeRegion(voteTable, index)">X</b-button></td>
          </tr>
          <tr><th class="growtable"><b-button size="sm"
            v-b-tooltip.hover.bottom.v-primary.ds500 title="Add region"
            @click="addRegion(voteTable)">
            <span class="add-button-symbol">+</span></b-button></th></tr>
        </tbody>
      </table>
    </div>
    <b-alert :show="Boolean(renameError)">{{ renameError }}</b-alert>
  </div>
</template>

<script>
import {addRegion, renameRegion, removeRegion} from "../voteTable.js"
export default {
  props: {voteTable: {type: Object, required: true}},
  data: () => ({renameError: ""}),
  methods: {
    addRegion,
    removeRegion,
    rename(index, event) {
      this.renameError = renameRegion(this.voteTable, index, event.target.value)
      event.target.value = this.voteTable.regions[index].abbreviation
    },
  },
}
</script>
