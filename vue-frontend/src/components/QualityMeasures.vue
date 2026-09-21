<template>
<div class="table-scroll quality-measures-scroll">
  <table style="position:relative">
    <thead> 
      <tr>                                      <!-- STATISTICS HEADING -->
        <th class="firstcol top quality-heading">{{group_titles["topLeft"]}}</th>
        <template v-for="stat in stats" :key="stat">
          <th :colspan="statColumnCount(stat)" class="top">
            {{stat_headings[stat]}}
          </th>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="(id, index) in group_ids" :key="id">
        <template v-if="show[id]">
          <tr v-if="group_titles[id] || headingType[id]=='systems'">
            <th :class="groupclass(id)">
              {{group_titles[id]}}                     <!-- GROUP TITLE -->
            </th>
            <template v-if="headingType[id]=='systems'">
              <template v-for="stat in stats" :key="stat">
                <template v-for="(sysname, s) in statColumnNames(stat, id)" :key="s">
                  <th :class="sysclass(s, stat, id)"
                      :title="columnTitle(stat, s, id)">
                    {{sysname}}
                  </th>
                </template>
              </template>
            </template>
            <template v-else-if="headingType[id]=='stats'">  <!-- STAT HEADING -->
              <template v-for="stat in stats" :key="stat">
                <th :colspan="statColumnCount(stat, id)" class="top">
                  {{stat_headings[stat]}}
                </th>
              </template>
            </template>
            <template v-else>                               <!-- NO HEADING -->
              <th :colspan="totalDataColumns" class="gap"></th>
            </template>
          </tr>
          <tr v-for="(row, rowidx) in vuedata[id]"
              :key="id + rowidx">
            <td class="firstcol">
              {{row["rowtitle"]}}
            </td>
            <template v-for="stat in stats" :key="stat">
              <template v-for="(entry, s) in row[stat]" :key="s">
                <td :class="sysclass(s, stat, id)">
                  {{format(entry)}}
                </td>
              </template>
            </template>
          </tr>
          <tr v-if="id in footnotes">
            <td class="firstcol" :colspan="1 + totalDataColumns">
              {{footnotes[id]}}
            </td>
          </tr>
          <tr v-if="vuedata[id].length>0">
            <td class="firstcol blank"></td>
          </tr>
        </template>
      </template>
      <tr><td class="firstcol blank"></td></tr>
    </tbody>
  </table>
</div>
</template>

<script>
import { mapState } from "vuex"
import { formatEstimateWithCi } from "../numberFormat.js"

export default {
  props: [
    "vuedata",
    "stats",
    "stat_headings",
    "system_names",
    "group_ids",
    "group_titles",
    "footnotes",
    "show",
  ],
  computed: {
    ...mapState(["display_settings"]),
    nsys: function() {return this.system_names.length},
    totalDataColumns: function() {
      return this.stats.reduce((total, stat) =>
        total + this.statColumnCount(stat), 0)
    },
    headingType: function() {return this.vuedata.headingType}
  },
  methods: {
    format(entry) {
      if (entry === null || typeof entry !== "object") return entry
      const digits = entry.integer ? 0 : this.display_settings.fractional_digits
      return formatEstimateWithCi(
        entry.value, entry.ci, digits, this.display_settings)
    },
    groupHasPairedDifference(stat, groupId) {
      return stat === "avg" && this.vuedata.has_paired_difference &&
        !this.vuedata.groups_without_paired_difference?.includes(groupId)
    },
    statColumnCount(stat, groupId=null) {
      return this.nsys + (
        this.groupHasPairedDifference(stat, groupId) ? 1 : 0)
    },
    statColumnNames(stat, groupId) {
      const names = [...this.system_names]
      if (this.groupHasPairedDifference(stat, groupId)) {
        names.splice(2, 0, "Difference")
      }
      return names
    },
    columnTitle(stat, index, groupId) {
      if (this.groupHasPairedDifference(stat, groupId) && index === 2) {
        return this.vuedata.difference_tooltip
      }
      return null
    },
    sysclass: function(s, stat, groupId) {
      if (s==this.statColumnCount(stat, groupId)-1) return "last"
      else return "middle"
    },
    groupclass: function(id) {
      if (this.headingType[id] == 'systems')
        return "firstcol"
      else
        return "firstcol top"
    }
  }
}
</script>

<style scoped>
table {
  table-layout: auto;
  font-size:90%;
  border-collapse:collapse;
  border-spacing:0;
}

th, td {
  white-space:nowrap;  
  border:1px solid #c7c7c7;
  padding: 2px 6px 3px 6px;
  border-left-width:0
}

th {
  font-weight:bold;
  background: #eee;
  text-align:center;
}

.quality-heading {
  white-space: pre-line;
}

th.top {
  border-top-width: 0px;
}

th:not(.top),td:not(.top) {
  border-top-width:0;
}

td {
  text-align:right;
}

.firstcol {
  text-align:left;
  position: sticky;
  background: #eee;
  left: 0;
}

.gap {
  background: white;
  border-right-width:0;
}

.middle {
  border-right-width:0;
}

.firstcol.top {
  border-top-width:0
}

.firstcol.topleft {
  border-top-width:0;
  background: white;
}

.blank {
  border-right-width:0;
  border-bottom-width:0;
  border-left-width:0;
  border-right-width:0;
  background: white;
  padding:6px
}

</style>
