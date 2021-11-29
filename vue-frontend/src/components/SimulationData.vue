<template>
<b-container fluid>
  <b-alert :show="methods.length == 0">
    Run simulation to get results.
  </b-alert>
  <table v-if="data.length > 0" class="simulationdata">
    <tr class="methods">
      <th class="topleft">
      </th>
      <th colspan="6"
        v-for="(system, idx) in data"
        class="methodname"
      >
        <div>{{ system.name }}</div>
      </th>
    </tr>
    <tr>
      <th class="measurename">Adjustment method</th>
      <td colspan="6"
        class="methoddata"
        v-for="(system, idx) in data"
      >
        {{system.method}}
      </td>
    </tr>
    <tr>
      <th class="topleft"></th>
      <template v-for="(system, sidx) in data">
        <th class="methodname">Average</th>
        <th class="methodname">Min</th>
        <th class="methodname">Max</th>
        <th class="methodname">Std. deviation</th>
        <th class="methodname">Skewness</th>
        <th class="methodname">Kurtosis</th>
      </template>
    </tr>
    <tr>
      <th class="measurename">
        <div>Comparison to other seat allocations</div>
      </th>
    </tr>
    <tr>
      <th class="measurename">
        <div>Sum of absolute differences of lists for tested method and:</div>
      </th>
    </tr>
    <tr v-for="midx in list_deviation_measures">
      <td class="measurename">
          {{ measures[midx] }}
      </td>
      <template v-for="(system, sidx) in data">
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["avg"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["min"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["max"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["std"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["skw"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["kur"].toFixed(4) }}
        </td>
      </template>
    </tr>
    <tr>
      <th class="measurename">
        <div>Sum of absolute differences of national totals for tested method and:</div>
      </th>
    </tr>
    <tr v-for="midx in totals_deviation_measures">
      <td class="measurename">
          {{ measures[midx] }}
      </td>
      <template v-for="(system, sidx) in data">
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["avg"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["min"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["max"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["std"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["skw"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["kur"].toFixed(4) }}
        </td>
      </template>
    </tr>
    <tr>
      <th class="measurename">
        <div>Quality indices (the higher the better):</div>
      </th>
    </tr>
    <tr v-for="midx in standardized_measures">
      <td class="measurename">
          {{ measures[midx] }}
      </td>
      <template v-for="(system, sidx) in data">
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["avg"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["min"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["max"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["std"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["skw"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["kur"].toFixed(4) }}
        </td>
      </template>
    </tr>
    <tr>
      <th class="measurename">
        <div>Comparison to ideal seat shares (the lower the better):</div>
      </th>
    </tr>
    <tr v-for="midx in ideal_comparison_measures">
      <td class="measurename">
          {{ measures[midx] }}
      </td>
      <template v-for="(system, sidx) in data">
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["avg"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["min"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["max"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["std"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["skw"].toFixed(4) }}
        </td>
        <td class="methoddata">
          {{ data[sidx]["measures"][midx]["kur"].toFixed(4) }}
        </td>
      </template>
    </tr>
  </table>
</b-container>
</template>
<script>
export default {
  props: [
    "testnames",
    "measures",
    "list_deviation_measures",
    "totals_deviation_measures",
    "standardized_measures",
    "ideal_comparison_measures",
    "methods",
    "data"
  ]
}
</script>
