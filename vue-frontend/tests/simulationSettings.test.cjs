const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

const filename = resolve(__dirname, '../src/SimulationSettings.vue')
const {descriptor} = parse(readFileSync(filename, 'utf8'))

test('simulation settings template compiles with the required controls', () => {
  const {errors} = compileTemplate({
    source: descriptor.template.content,
    filename,
    id: 'simulation-settings-test',
  })

  assert.deepEqual(errors, [])
  assert.match(descriptor.template.content,
    /v-model="sim_settings\.entropy_score"/)
  assert.match(descriptor.template.content,
    /v-if="vote_table\.party_vote_info\.specified"/)
})

test('sensitivity controls stay visible and support editing CoVs', () => {
  assert.match(descriptor.template.content,
    /v-model="sim_settings\.sensitivity"/)
  assert.doesNotMatch(descriptor.template.content,
    /v-if="sim_settings\.sensitivity"/)
  assert.match(descriptor.template.content,
    /v-model\.number="sim_settings\.sensitivity_covs\[index\]"/)
  for (const action of ['sortSensitivityCovs', 'addSensitivityCov', 'removeSensitivityCov']) {
    assert.ok(descriptor.template.content.includes(action))
  }
})

test('sensitivity CoVs sort after editing and adding, but invalid values stay visible', () => {
  const script = descriptor.script.content
    .replace(/^import \{ mapState \} from 'vuex';\s*/m, '')
    .replace('export default', 'return')
  const component = new Function('mapState', script)(() => ({}))
  const covs = [3, 1, 2]
  const instance = {
    sim_settings: {sensitivity_covs: covs},
    sortSensitivityCovs: component.methods.sortSensitivityCovs,
  }

  instance.sortSensitivityCovs()
  assert.deepEqual(covs, [1, 2, 3])

  covs.splice(0, covs.length, 3, 1, 1)
  instance.sortSensitivityCovs()
  assert.deepEqual(covs, [3, 1, 1])

  covs.splice(0, covs.length, 3, 2, 1)
  component.methods.addSensitivityCov.call(instance)
  assert.deepEqual(covs, [1, 2, 3, 4])

  covs.splice(0, covs.length, 0.1)
  component.methods.addSensitivityCov.call(instance)
  assert.deepEqual(covs, [0.1, 0.2])
  component.methods.addSensitivityCov.call(instance)
  assert.deepEqual(covs, [0.1, 0.2, 0.3])
})
