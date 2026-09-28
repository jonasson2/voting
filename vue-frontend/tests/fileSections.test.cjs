const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {runInNewContext} = require('node:vm')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

const source = readFileSync(resolve(__dirname, '../src/store.js'), 'utf8')
  .replace(/^import .*\n/gm, '')
  .replace('export default store', 'store')

function uploadStore() {
  const requests = []
  const store = runInNewContext(source, {
    Vue: {
      http: {post(path) {
        const request = {}
        request.promise = new Promise(resolve => { request.resolve = resolve })
        requests.push({path, ...request})
        return request.promise
      }},
      nextTick(callback) { callback() },
    },
    Vuex: {Store: class { constructor(options) { Object.assign(this, options) } }},
    defaultDisplaySettings: () => ({}),
    window: {addEventListener() {}},
  })
  const context = {
    state: store.state,
    commit(name, value) { store.mutations[name](store.state, value) },
    dispatch(name, payload) {
      if (name === 'recalc_sys_const') return
      return store.actions[name](context, payload)
    },
  }
  return {store, context, requests}
}

test('section uploads change only their own state; all upload changes all three', async () => {
  const {store, context, requests} = uploadStore()
  context.state.vote_table = {name: 'old votes'}
  context.state.systems = [{name: 'old system'}]
  context.state.sim_settings = {simulation_count: 10}

  store.actions.uploadElectoralSystems(context, {formData: {}, replace: true})
  assert.equal(requests[0].path, 'api/systems/upload/')
  requests[0].resolve({body: {}, data: {systems: [{name: 'new system'}]}})
  await requests[0].promise
  assert.equal(context.state.systems[0].name, 'new system')
  assert.equal(context.state.vote_table.name, 'old votes')
  assert.equal(context.state.sim_settings.simulation_count, 10)

  store.actions.uploadSimulationSettings(context, {})
  assert.equal(requests[1].path, 'api/simulation-settings/upload/')
  requests[1].resolve({body: {}, data: {sim_settings: {simulation_count: 20}}})
  await requests[1].promise
  assert.equal(context.state.sim_settings.simulation_count, 20)
  assert.equal(context.state.systems[0].name, 'new system')
  assert.equal(context.state.vote_table.name, 'old votes')

  // updateVoteTable uses vote-table helpers, so inspect the action's mutations.
  const mutations = []
  context.commit = (name, value) => mutations.push({name, value})
  store.actions.uploadAll(context, {formData: {}, filename: 'all.json'})
  assert.equal(requests[2].path, 'api/uploadall/')
  requests[2].resolve({body: {}, data: {
    vote_table: {name: 'all votes'}, systems: [{name: 'all system'}],
    sim_settings: {simulation_count: 30},
  }})
  await requests[2].promise
  assert.deepEqual(mutations.filter(item => [
    'updateVoteTable', 'updateSystems', 'updateSimSettings',
  ].includes(item.name)).map(item => item.name), [
    'updateVoteTable', 'updateSystems', 'updateSimSettings',
  ])
})

test('reset copies the initialized defaults', () => {
  const {store, context} = uploadStore()
  context.state.default_sim_settings = {simulation_count: 200, sensitivity_covs: [1, 2, 3]}
  context.state.sim_settings = {simulation_count: 10, sensitivity_covs: [8]}
  store.actions.resetSimulationSettings(context)
  assert.equal(context.state.sim_settings.simulation_count, 200)
  context.state.sim_settings.sensitivity_covs.push(4)
  assert.equal(context.state.default_sim_settings.sensitivity_covs.length, 3)
})

test('simulation toolbar offers all five controls', () => {
  const filename = resolve(__dirname, '../src/Simulate.vue')
  const {descriptor} = parse(readFileSync(filename, 'utf8'))
  const {errors} = compileTemplate({
    source: descriptor.template.content, filename, id: 'file-sections-test',
  })
  assert.deepEqual(errors, [])
  for (const label of ['Upload', 'Download', 'Reset to defaults',
    'Upload all', 'Download all']) {
    assert.match(descriptor.template.content, new RegExp(`>${label}</b-button>`))
  }
})
