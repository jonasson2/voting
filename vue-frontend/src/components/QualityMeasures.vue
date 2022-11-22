<template>
<div style="margin:0px 15px; overflow-x:scroll">
  <table style="position:relative">
    <thead> 
      <tr>                                      <!-- STATISTICS HEADING -->
        <th class="firstcol top"> {{group_titles["topLeft"]}} </th>
        <template v-for="stat in stats">
          <th :colspan="nsys" :key="stat" class="top">
            {{stat_headings[stat]}}
          </th>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="(id, index) in group_ids">
        <template v-if="show[id]">
          <tr v-if="headingType[id]=='stats'">
            <td class="firstcol blank"></td>
          </tr>
          <tr>
            <th :class="groupclass(id)">
              {{group_titles[id]}}                     <!-- GROUP TITLE -->
            </th>
            <template v-if="headingType[id]=='systems'">
              <template v-for="idx in nstat">
                <template v-for="(sysname, s) in system_names"> <!-- SYS HEADING -->
                  <th :class="sysclass(s)">
                    {{sysname}}
                  </th>
                </template>
              </template>
            </template>
            <template v-else-if="headingType[id]=='stats'">  <!-- STAT HEADING -->
              <template v-for="stat in stats">
                <th :colspan="nsys" :key="stat" class="top">
                  {{stat_headings[stat]}}
                </th>
              </template>
            </template>
            <template v-else>                               <!-- NO HEADING -->
              <th :colspan="nsys*nstat" class="gap"></th>
            </template>
          </tr>
          <tr v-for="(row, rowidx) in vuedata[id]"
              :key="id + rowidx">
            <td class="firstcol">
              {{row["rowtitle"]}}
            </td>
            <template v-for="stat in stats">
              <template v-for="s in nsys">
                <td :class="sysclass(s-1)">
                  {{row[stat][s - 1]}}
                </td>
              </template>
            </template>
          </tr>
          <tr v-if="id in footnotes">
            {{footnotes[id]}}
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
    nstat: function() {return this.stats.length},
    nsys:  function() {return this.system_names.length},
    headingType: function() {return this.vuedata.headingType}
  },
  methods: {
    sysclass: function(s) {
      if (s==this.nsys-1) return "last"
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
