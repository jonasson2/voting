<template>
  <input
    v-bind="$attrs"
    :value="displayValue"
    type="text"
    v-autowidth="{ maxWidth, minWidth }"
    inputmode="numeric"
    @focus="focused = true"
    @blur="focused = false"
    @beforeinput="checkInsertion"
    @paste="checkPaste"
    @input="updateValue"
  />
</template>

<script>
import { mapState } from "vuex"
import { formatNumber, parseInteger, validIntegerEntry } from "../numberFormat.js"

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
    insertedValue(element, text) {
      return element.value.slice(0, element.selectionStart)
        + text
        + element.value.slice(element.selectionEnd)
    },
    checkInsertion(event) {
      if (event.data === null) return
      if (!validIntegerEntry(
        this.insertedValue(event.target, event.data), this.allowUnlimited)) {
        event.preventDefault()
      }
    },
    checkPaste(event) {
      const text = event.clipboardData.getData("text")
      if (!validIntegerEntry(
        this.insertedValue(event.target, text), this.allowUnlimited)) {
        event.preventDefault()
      }
    },
    updateValue(event) {
      this.$emit("input", parseInteger(event.target.value, this.allowUnlimited))
    },
  },
}
</script>
