<template>
  <input
    v-bind="$attrs"
    :value="displayValue"
    :aria-invalid="invalid || undefined"
    :class="{'integer-input-invalid': invalid}"
    type="text"
    v-autowidth="{ maxWidth, minWidth }"
    inputmode="numeric"
    @focus="startEditing"
    @blur="finishEditing"
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
    return {focused: false, draft: ""}
  },
  computed: {
    ...mapState(["display_settings"]),
    displayValue() {
      if (this.focused) return this.draft
      if (!Number.isInteger(this.value)) return this.value
      return formatNumber(this.value, 0, this.display_settings)
    },
    invalid() {
      return !validIntegerEntry(
        this.focused ? this.draft : this.value,
        this.display_settings,
        this.allowUnlimited,
      )
    },
  },
  methods: {
    startEditing(event) {
      this.draft = String(this.value ?? "")
      this.focused = true
      event.target.value = this.draft
    },
    finishEditing() {
      this.focused = false
      this.$emit("input", parseInteger(
        this.draft,
        this.display_settings,
        this.allowUnlimited,
      ))
    },
    updateValue(event) {
      this.draft = event.target.value
      this.$emit("input", parseInteger(
        this.draft,
        this.display_settings,
        this.allowUnlimited,
      ))
    },
  },
}
</script>
