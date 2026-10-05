<template>
<div class="table-scroll quality-measures-scroll">
  <table style="position:relative">
    <thead> 
      <tr class="block-heading">                <!-- STATISTICS HEADING -->
        <th rowspan="2" class="firstcol quality-heading">
          {{group_titles["topLeft"]}}
        </th>
        <template v-for="stat in stats" :key="stat">
          <th :colspan="nsys" class="title-rule stat-edge">
            {{stat_headings[stat]}}
          </th>
        </template>
      </tr>
      <tr>
        <template v-for="stat in statsForGroup('shareTitle')" :key="stat">
          <template v-for="(sysname, s) in system_names" :key="s">
            <th class="system-heading title-rule"
                :class="sysclass(s)">
              {{sysname}}
            </th>
          </template>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="id in group_ids" :key="id">
        <template v-if="show[id] && id !== 'shareTitle'">
          <tr v-if="group_titles[id] || headingType[id]=='systems'"
              :class="{'block-heading': group_titles[id]}">
            <th v-if="group_titles[id]" class="firstcol"
                :rowspan="headingType[id] === 'stats' ? 2 : null">
              {{group_titles[id]}}                     <!-- GROUP TITLE -->
            </th>
            <template v-if="headingType[id]=='systems'">
              <template v-for="stat in statsForGroup(id)" :key="stat">
                <template v-for="(sysname, s) in system_names" :key="s">
                  <th class="system-heading title-rule"
                      :class="sysclass(s)">
                    {{sysname}}
                  </th>
                </template>
              </template>
            </template>
            <template v-else-if="headingType[id]=='stats'">  <!-- STAT HEADING -->
              <template v-for="stat in statsForGroup(id)" :key="stat">
                <th :colspan="nsys" class="title-rule stat-edge">
                  {{stat_headings[stat]}}
                </th>
              </template>
            </template>
            <template v-else>                               <!-- NO HEADING -->
              <td :colspan="dataColumnsForGroup(id)"
                  :class="{'title-rule': !vuedata.group_messages?.[id]}"></td>
            </template>
          </tr>
          <tr v-if="vuedata.group_messages?.[id]">
            <td class="group-message" :colspan="1 + totalDataColumns">
              <span class="footnote-text">{{vuedata.group_messages[id]}}</span>
            </td>
          </tr>
          <tr v-for="(row, rowidx) in vuedata[id]"
              :key="id + rowidx"
              :class="{
                'subgroup-start': row.subgroup_start,
                'block-end': rowidx === vuedata[id].length - 1,
              }">
            <td class="firstcol" v-b-tooltip.hover.top.v-primary.ds500
                :title="row.tooltip">
              {{row["rowtitle"]}}
            </td>
            <template v-for="stat in statsForGroup(id)" :key="stat">
              <template v-for="(entry, s) in row[stat]" :key="s">
                <td :class="sysclass(s)">
                  {{format(entry)}}
                </td>
              </template>
            </template>
          </tr>
          <tr v-if="id in footnotes">
            <td class="footnote"
                :colspan="1 + totalDataColumns">
              <span class="footnote-text">{{footnotes[id]}}</span>
            </td>
          </tr>
          <tr v-if="vuedata[id].length > 0 || vuedata.group_messages?.[id]"
              class="section-spacer"
              aria-hidden="true">
            <td :colspan="1 + totalDataColumns">&nbsp;</td>
          </tr>
        </template>
      </template>
    </tbody>
  </table>
</div>
</template>

<script>
import { mapState } from "vuex"
import { formatNumber } from "../numberFormat.js"

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
      return this.stats.length * this.nsys
    },
    headingType: function() {return this.vuedata.headingType}
  },
  methods: {
    format(entry) {
      if (entry === null || typeof entry !== "object") return entry
      const digits = entry.percentage
        ? this.display_settings.percentage_digits
        : entry.integer ? 0 : this.display_settings.fractional_digits
      const display = value => formatNumber(
        entry.percentage ? value * 100 : value, digits, this.display_settings)
      const value = display(entry.value)
      return entry.ci === null
        ? value
        : `${value} ± ${display(entry.ci)}`
    },
    statsForGroup(groupId) {
      return this.vuedata.group_stats?.[groupId] || this.stats
    },
    dataColumnsForGroup(groupId) {
      return this.statsForGroup(groupId).length * this.nsys
    },
    sysclass(s) {
      return {'stat-edge': s === this.nsys - 1}
    },
  }
}
</script>

<style scoped>
table {
  --rule: 1.5px solid #c7c7c7;
  table-layout: auto;
  font-size:90%;
  /* Collapsed borders detach from sticky cells during horizontal scrolling. */
  border-collapse:separate;
  border-spacing:0;
}

th, td {
  white-space:nowrap;  
  border:0;
  padding: 2px 6px 3px 6px;
}

th {
  font-weight:bold;
  background: #eee;
  text-align:center;
}

.quality-heading {
  white-space: pre-line;
}

td, .system-heading {
  text-align:right;
}

.title-rule,
th.firstcol,
tr.block-end > td {
  border-bottom:var(--rule);
}

.block-heading > th {
  border-top:var(--rule);
}

tr.subgroup-start > td {
  border-top:var(--rule);
}

.stat-edge,
.firstcol {
  border-right:var(--rule);
}

.firstcol,
.footnote-text {
  position: sticky;
  z-index: 1;
  left: 0;
}

.firstcol {
  text-align:left;
  background: #eee;
  border-left:var(--rule);
}

th.firstcol {
  vertical-align:middle;
}

.footnote,
.group-message {
  text-align: left;
}

.footnote-text {
  display: inline-block;
  left: 6px;
  background: white;
}

</style>
