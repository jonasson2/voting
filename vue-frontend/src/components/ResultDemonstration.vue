<template>
  <b-container fluid v-if="table.steps.length > 0">
    <table class="demomatrix">
      <tr v-if="table.sup_headers">
        <th v-for="sh in table.sup_headers" v-bind:colspan="sh.colspan">
          {{ sh.text }}
        </th>
      </tr>
      <tr>
        <th v-for="header in table.headers">
          {{ header }}
        </th>
      </tr>
      <tr v-for="(step, stepidx) in table.steps">
        <template v-for="(col, colidx) in step">
          <td>
            <span style="white-space: pre-wrap;">{{col}}</span>
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
  }
}
</script>
