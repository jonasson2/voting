<template>
  <input
    v-bind="$attrs"
    :value="displayValue"
    type="text"
    v-autowidth="{ maxWidth, minWidth }"
    @focus="focused = true"
    @blur="focused = false"
    @input="updateValue"
  />
</template>

<script>
import { mapState } from "vuex"
import { formatNumber, parseInteger } from "../numberFormat.js"

export default {
  inheritAttrs: false,
  props: {
    value: {required: true},
    allowUnlimited: {type: Boolean, default: false},
    maxWidth: {type: String, default: "300px"},
    minWidth: {type: String, default: "25px"},
  },
  emits: ["input"],
  data() {
    return {focused: false}
  },
  computed: {
    ...mapState(["display_settings"]),
    displayValue() {
      if (this.focused || !Number.isInteger(this.value)) {
        return this.value
      }
      return formatNumber(this.value, 0, this.display_settings)
    },
  },
  methods: {
    updateValue(event) {
      this.$emit("input", parseInteger(event.target.value, this.allowUnlimited))
    },
  },
}
</script>
