<template>
  <b-container fluid class="settings-pane">
    <h3>Settings</h3>
    <div class="settings-grid">
      <label for="number-separators">Thousands and decimal separators</label>
      <b-form-select
        id="number-separators"
        v-model="separatorStyle"
        :options="separatorOptions"
      />
      <label for="fractional-digits">Fractional digits in results</label>
      <b-form-input
        id="fractional-digits"
        class="precision-input"
        v-model.number="fractionalDigits"
        type="number"
        min="0"
        max="10"
        step="1"
      />
      <label for="percentage-digits">Fractional digits in percentages</label>
      <b-form-input
        id="percentage-digits"
        class="precision-input"
        v-model.number="percentageDigits"
        type="number"
        min="0"
        max="10"
        step="1"
      />
    </div>
  </b-container>
</template>

<script>
import { mapMutations, mapState } from "vuex"
import { NUMBER_SEPARATOR_OPTIONS } from "./numberFormat.js"

export default {
  computed: {
    ...mapState(["display_settings"]),
    separatorOptions() {
      return NUMBER_SEPARATOR_OPTIONS.map(({value, text}) => ({value, text}))
    },
    separatorStyle: {
      get() {
        const option = NUMBER_SEPARATOR_OPTIONS.find(item =>
          item.thousands === this.display_settings.thousands_separator
            && item.decimal === this.display_settings.decimal_separator
        )
        return option ? option.value : NUMBER_SEPARATOR_OPTIONS[0].value
      },
      set(value) {
        const option = NUMBER_SEPARATOR_OPTIONS.find(item => item.value === value)
        this.updateDisplaySettings({
          ...this.display_settings,
          thousands_separator: option.thousands,
          decimal_separator: option.decimal,
        })
      },
    },
    fractionalDigits: {
      get() {
        return this.display_settings.fractional_digits
      },
      set(value) {
        this.updateDisplaySettings({
          ...this.display_settings,
          fractional_digits: value,
        })
      },
    },
    percentageDigits: {
      get() {
        return this.display_settings.percentage_digits
      },
      set(value) {
        this.updateDisplaySettings({
          ...this.display_settings,
          percentage_digits: value,
        })
      },
    },
  },
  methods: mapMutations(["updateDisplaySettings"]),
}
</script>

<style scoped>
.settings-pane {
  padding: 0 16px 24px;
}

.settings-pane h3 {
  margin-left: 0;
}

.settings-grid {
  display: grid;
  grid-template-columns: max-content minmax(9rem, 13rem);
  align-items: center;
  gap: 12px 16px;
}

.settings-grid label {
  margin: 0;
}

.precision-input {
  width: 5rem;
}

@media (max-width: 480px) {
  .settings-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 5px;
  }

  .settings-grid label:not(:first-child) {
    margin-top: 10px;
  }
}
</style>
