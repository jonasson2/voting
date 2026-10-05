const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')

async function storeConfig(Vue = {}, axios = () => Promise.resolve()) {
  const numberSource = readFileSync(resolve(__dirname, '../src/numberFormat.js'), 'utf8')
  const {defaultDisplaySettings, normalizeDisplaySettings} = await import(
    `data:text/javascript;base64,${Buffer.from(numberSource).toString('base64')}`)
  const source = readFileSync(resolve(__dirname, '../src/store.js'), 'utf8')
    .replace(/^import .*$/gm, '')
    .replace('export default store', 'return store')
  return new Function('Vue', 'Vuex', 'defaultDisplaySettings', 'normalizeDisplaySettings',
    'axios', source)(Vue, {Store: function(config) {return config}},
      defaultDisplaySettings, normalizeDisplaySettings, axios)
}

test('Download all includes precision and omits separators', async () => {
  let request
  const store = await storeConfig({}, options => {
    request = options
    return Promise.resolve()
  })
  store.state.display_settings = {
    fractional_digits: 5, percentage_digits: 2,
    thousands_separator: '.', decimal_separator: ',',
  }
  await store.actions.saveAll({state: store.state, dispatch: async () => false})
  assert.deepEqual(request.data.display_settings,
    {fractional_digits: 5, percentage_digits: 2})
})

test('Upload all restores precision while retaining the current separators', async () => {
  for (const display_settings of [undefined, {fractional_digits: 5, percentage_digits: 2}]) {
    const response = {data: {vote_table: {}, systems: [], sim_settings: {}, display_settings},
      body: {}}
    const store = await storeConfig({http: {post: () => ({then: callback => callback(response)})}})
    store.state.display_settings.thousands_separator = '.'
    store.state.display_settings.decimal_separator = ','
    const before = {...store.state.display_settings}
    const context = {state: store.state, commit(name, value) {
      if (name === 'updateDisplaySettings') store.mutations[name](store.state, value)
    }}
    store.actions.uploadAll(context, {formData: {}, filename: 'all.json'})
    assert.deepEqual(store.state.display_settings, {...before, ...display_settings})
  }
})
