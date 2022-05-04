<template>
  <b-container fluid v-if="table.steps.length > 0">
    <table>
      <tr class="sup-headers" v-if="table.sup_header">
        <th v-bind:colspan="table.headers.length">
          {{table.sup_header}}
        </th>
      </tr>
      <tr>
        <th v-for="header in table.headers">
          {{ header }}
        </th>
      </tr>
      <tr v-for="(step, stepidx) in table.steps">
        <template v-for="(col, colidx) in step">
          <td :style="alignment(table.format[colidx])">
            <span style="white-space: pre-wrap;">{{format(col,colidx)}}</span>
          </td>
        </template>
      </tr>
    </table>
  </b-container>
  <b-container fluid v-else>
    <p>Table demonstrating the step-by-step allocation of adjustment seats
      is not applicable as the method finds the solution by iteration
    </p>
  </b-container>
</template>
<script>

export default {
  props: {
    "table": { default: { "headers": [], "steps": [] } },
  },
  methods: {
    alignment: function(c) {
      return "text-align: " + (c=="l" ? "left" : "center")
    },
    format: function(value, colidx) {
      var fmt = this.table.format[colidx]
      if (fmt == "%")
        return parseFloat(value*100).toFixed(3)+"%"
      let n = parseInt(fmt)
      if (isNaN(n)) return value
      return parseFloat(value).toFixed(n)
    }
  }
}
</script>

<style scoped>
th, td {
  border:        1px solid #ccc;
  text-align:    left;
  padding:       6px;
  table-layout:  auto;
  margin-bottom: 1em;
}

th {
  /* white-space: wrap; */
  text-align:  center;
  font-weight: 700;
}

.sup-headers th {
  text-align: center
}

tr:nth-child(even) {
  background-color: #f2f2f2;
}

</style>
