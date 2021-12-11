<template>
<div style="margin:0px 15px; overflow-x:scroll">
  <table style="position:relative">
    <thead> 
      <tr>                                      <!-- STATISTICS HEADING -->
        <td class="firstcol topleft"></td>
        <template v-for="stat in stats">
          <th :colspan="nsys" :key="stat" class="top">
            {{stat_headings[stat]}}
          </th>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="(id, index) in group_ids">
        <tr v-if="headingType[id]=='stats'">
          <td class="firstcol blank"></td>
        </tr>
        <tr>
          <td :class="groupclass(id)">
            {{group_titles[id]}}                     <!-- GROUP TITLE -->
          </td>
          <template v-if="headingType[id]=='systems'">
            <template v-for="idx in nstat">
              <template v-for="(sysname, s) in system_names"> 
                <td :class="sysclass(s)">
                  {{sysname}}
                </td>
              </template>
            </template>
          </template>
          <template v-else-if="headingType[id]=='stats'">
            <template v-for="stat in stats">
              <th :colspan="nsys" :key="stat" class="top">
                {{stat_headings[stat]}}
              </th>
            </template>
          </template>
          <template v-else>
            <th :colspan="nsys*nstat" class="topright"></th>
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
        <tr v-if="vuedata[id].length>0">
          <td class="firstcol gap"></td>
        </tr>
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
        return "firstcol bold"
      else
        return "firstcol bold top"
    }
  }
}
</script>

<style scoped>
table {
  table-layout: auto;
  font-size:90%;
  border-collapse:separate;
  border-spacing:0;
}

th, td {
  white-space:nowrap;  
  border:1px solid #ccc;
  padding: 2px 6px 3px 6px;
}

.bold {
  font-weight:bold
}

td {
  text-align:right;
}

.firstcol {
  text-align:left;
  position: sticky;
  left: 0;
  background: #fff;
}

th:not(.firstcol),td:not(.firstcol) {
  border-left: unset;
}

th {
  font-weight:bold;
  text-align:center;
}

th:not(.top),td:not(.top) {
  border-top:unset;
}

.topright {
  border-right:unset;
}

.middle {
  border-left:unset;
  border-right:unset;
}

.last {
  border-left:unset;
}

.topleft {
  border-left:unset;
  border-top:unset;
}

.bold{testweight:bold;}

.top {}

.blank {
  border:unset;
  padding:4px
}

.gap {
  border:unset;
  padding:4px;
}

</style>
