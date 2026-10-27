const assert = require('node:assert/strict')
const test = require('node:test')
const {createStore} = require('vuex')

async function helpers() {
  return {
    ...await import('../src/displayPreferences.js'),
    ...await import('../src/numberFormat.js'),
  }
}

function makeStore({defaultDisplaySettings, normalizeDisplaySettings}) {
  return createStore({
    state: {display_settings: defaultDisplaySettings(), vote_table: {name: 'My election'}},
    mutations: {
      updateDisplaySettings(state, settings) {
        state.display_settings = normalizeDisplaySettings(settings)
      },
      updateVotes(state) { state.vote_table.name = 'Another election' },
    },
  })
}

test('precision and separators survive a new browser session', async () => {
  const h = await helpers()
  const saved = new Map()
  const storage = {getItem: key => saved.get(key), setItem: (key, value) => saved.set(key, value)}
  for (const separators of h.NUMBER_SEPARATOR_OPTIONS) {
    const first = makeStore(h)
    h.installDisplayPreferences(first, storage)
    const settings = {fractional_digits: 5, percentage_digits: 3,
      thousands_separator: separators.thousands, decimal_separator: separators.decimal}
    first.commit('updateDisplaySettings', settings)
    assert.deepEqual(JSON.parse(saved.get(h.DISPLAY_STORAGE_KEY)), settings)
    const next = makeStore(h)
    h.installDisplayPreferences(next, storage)
    assert.deepEqual(next.state.display_settings, settings)
    assert.equal(h.formatNumber(1234.5, 5, next.state.display_settings),
      `1${separators.thousands === ' ' ? '\u202f' : separators.thousands}234${separators.decimal}50000`)
    assert.equal(next.state.vote_table.name, 'My election')
    const before = saved.get(h.DISPLAY_STORAGE_KEY)
    next.commit('updateVotes')
    assert.equal(saved.get(h.DISPLAY_STORAGE_KEY), before)
  }
})

test('saved preferences are normalized before use', async () => {
  const h = await helpers()
  const store = makeStore(h)
  h.installDisplayPreferences(store, {
    getItem: () => JSON.stringify({fractional_digits: 99, percentage_digits: -3,
      thousands_separator: '/', decimal_separator: '/', unknown: 'ignored'}),
    setItem() {},
  })
  assert.deepEqual(store.state.display_settings,
    {...h.defaultDisplaySettings(), fractional_digits: 10, percentage_digits: 0})
})

test('missing, malformed, blocked or full storage does not prevent editing', async () => {
  const h = await helpers()
  for (const value of [null, '{broken', 'null', '[]', 'false', '"text"', 'blocked']) {
    const store = makeStore(h)
    const storage = {
      getItem() { if (value === 'blocked') throw Error('blocked'); return value },
      setItem() { throw Error('full') },
    }
    assert.doesNotThrow(() => h.installDisplayPreferences(store, storage))
    assert.deepEqual(store.state.display_settings, h.defaultDisplaySettings())
    assert.doesNotThrow(() => store.commit('updateDisplaySettings',
      {...store.state.display_settings, fractional_digits: 4}))
    assert.equal(store.state.display_settings.fractional_digits, 4)
  }
})
