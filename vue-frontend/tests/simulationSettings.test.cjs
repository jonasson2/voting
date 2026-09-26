const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

const filename = resolve(__dirname, '../src/SimulationSettings.vue')
const {descriptor} = parse(readFileSync(filename, 'utf8'))

test('entropy-score calculation is an explicit simulation setting', () => {
  const {errors} = compileTemplate({
    source: descriptor.template.content,
    filename,
    id: 'simulation-settings-test',
  })

  assert.deepEqual(errors, [])
  assert.match(descriptor.template.content,
    /v-model="sim_settings\.entropy_score"/)
  assert.match(descriptor.template.content,
    /Calculate entropy score\?/)
  assert.match(descriptor.template.content,
    /v-if="vote_table\.party_vote_info\.specified" class="simulation-setting-row"[\s\S]*?simulation-party-rsd/)
  assert.match(descriptor.template.content,
    /v-if="vote_table\.party_vote_info\.specified" class="simulation-setting-row"[\s\S]*?simulation-party-corr/)
})

test('sensitivity settings expose nested simulation and CoV controls', () => {
  const {errors} = compileTemplate({
    source: descriptor.template.content,
    filename,
    id: 'simulation-sensitivity-settings-test',
  })

  assert.deepEqual(errors, [])
  assert.match(descriptor.template.content,
    /v-model="sim_settings\.sensitivity"/)
  assert.match(descriptor.template.content,
    /v-model\.number="sim_settings\.sensitivity_simulation_count"/)
  assert.match(descriptor.template.content,
    /v-model="sim_settings\.sensitivity_gen_method"/)
  assert.match(descriptor.template.content,
    /v-for="\(cov, index\) in sim_settings\.sensitivity_covs"/)
  assert.match(descriptor.template.content,
    /v-model\.number="sim_settings\.sensitivity_covs\[index\]"/)
  assert.match(descriptor.template.content, /@click="addSensitivityCov"/)
  assert.match(descriptor.template.content,
    /v-if="index === sim_settings\.sensitivity_covs\.length - 1"/)
  assert.match(descriptor.template.content, /@click="removeSensitivityCov\(index\)"/)
})
