<template>
<div class="table-scroll quality-measures-scroll">
  <table style="position:relative">
    <thead> 
      <tr class="block-heading">                <!-- STATISTICS HEADING -->
        <th rowspan="2" colspan="2" class="block-title simulator-title">{{vuedata.initial_title}}</th>
        <template v-for="stat in stats" :key="stat">
          <th :colspan="nsys" class="data-heading stat-edge"
              :class="{'header-start': stat === stats[0]}">
            {{stat_headings[stat]}}
          </th>
        </template>
      </tr>
      <tr>
        <template v-for="stat in statsForGroup('shareTitle')" :key="stat">
          <template v-for="(sysname, s) in system_names" :key="s">
            <th class="system-heading data-heading"
                :class="[sysclass(s), {'header-start': s === 0 && stat === statsForGroup('shareTitle')[0]}]">
              {{sysname}}
            </th>
          </template>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="id in group_ids" :key="id">
        <template v-if="groupVisible(id)">
          <tr v-if="vuedata.block_headers?.[id]" class="block-heading">
            <th class="block-title simulator-title" colspan="2">{{vuedata.block_headers[id]}}</th>
            <template v-for="stat in statsForGroup(id)" :key="stat">
              <th v-for="(sysname, s) in system_names" :key="s"
                  class="system-heading data-heading"
                  :class="[sysclass(s), {'header-start': s === 0 && stat === statsForGroup(id)[0]}]">
                {{sysname}}
              </th>
            </template>
          </tr>
          <tr v-if="!vuedata.side_titles?.[id] && (group_titles[id] || headingType[id]=='systems')"
              :class="{'block-heading': group_titles[id]}">
            <th v-if="group_titles[id]" class="firstcol" colspan="2"
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
            <th v-if="vuedata.side_titles?.[id]" class="section-title">
              {{group_titles[id]}}
            </th>
            <td class="group-message"
                :colspan="(vuedata.side_titles?.[id] ? 1 : 2) + dataColumnsForGroup(id)">
              <span class="footnote-text">{{vuedata.group_messages[id]}}</span>
            </td>
          </tr>
          <tr v-for="(row, rowidx) in (vuedata.group_messages?.[id] ? [] : visibleRows(id))"
              :key="id + rowidx"
              :class="{
                'block-start': vuedata.side_titles?.[id] && rowidx === 0,
                'subgroup-start': row.subgroup_start,
                'block-end': rowidx === visibleRows(id).length - 1,
              }">
            <th v-if="vuedata.side_titles?.[id] && rowidx === 0"
                class="section-title" :rowspan="visibleRows(id).length">
              {{group_titles[id]}}
            </th>
            <td v-else-if="!vuedata.side_titles?.[id]" class="section-blank"></td>
            <td class="firstcol">
              <span v-b-tooltip.hover.top.v-primary.ds500 :title="row.tooltip">
                {{row["rowtitle"]}}
              </span>
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
                :colspan="2 + totalDataColumns">
              <span class="footnote-text">{{footnotes[id]}}</span>
            </td>
          </tr>
          <tr v-if="!vuedata.block_continues?.[id] && (vuedata[id].length > 0 || vuedata.group_messages?.[id])"
              class="section-spacer"
              aria-hidden="true">
            <td :colspan="2 + totalDataColumns">&nbsp;</td>
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
    ...mapState(["display_settings", "sim_settings"]),
    nsys: function() {return this.system_names.length},
    totalDataColumns: function() {
      return this.stats.length * this.nsys
    },
    headingType: function() {return this.vuedata.headingType}
  },
  methods: {
    optionEnabled(option) {
      return !option || (this.sim_settings?.[option]
        ?? this.vuedata.display_options?.[option] ?? false)
    },
    visibleRows(id) {
      return this.vuedata[id].filter(row => this.optionEnabled(row.option))
    },
    groupVisible(id) {
      return this.show[id] && this.optionEnabled(this.vuedata.group_options?.[id])
    },
    format(entry) {
      if (entry === null || typeof entry !== "object") return entry
      const digits = entry.percentage
        ? this.display_settings.percentage_digits
        : entry.integer ? 0 : this.display_settings.fractional_digits
      const display = value => formatNumber(
        entry.percentage ? value * 100 : value, digits, this.display_settings)
      const value = display(entry.value)
      if (entry.ci === null) return value + (entry.percentage ? '%' : '')
      const interval = `${value} ± ${display(entry.ci)}`
      return entry.percentage ? `(${interval})%` : interval
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
  font-size: 1rem;
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

.section-title {
  white-space: pre-line;
  text-align: left;
  vertical-align: top;
  border-left: var(--rule);
  border-right: var(--rule);
  border-bottom: var(--rule);
  min-width: 145px;
}

td, .system-heading {
  text-align:right;
}

.title-rule,
th.firstcol,
tr.block-end > td:not(.section-blank) {
  border-bottom:var(--rule);
}

/* Numeric headers own their frame, even beside an unbordered block title.
   The first numeric cell owns the left edge; stat-edge owns the right edges. */
.data-heading {
  border-top: var(--rule);
  border-bottom: var(--rule);
}

.header-start {
  border-left: var(--rule);
}

.block-heading > th.firstcol {
  border-top: var(--rule);
}

.block-title {
  background: transparent;
  border: 0;
  font-size: 1.4rem;
  font-weight: normal;
  text-align: left;
  vertical-align: bottom;
  white-space: normal;
  padding-bottom: 6px;
}

tr.block-start > th,
tr.block-start > td {
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
