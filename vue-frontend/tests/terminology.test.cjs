const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const test = require('node:test')

async function helpers() {
  const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../src/terminology.json')))
  const source = fs.readFileSync(path.join(__dirname, '../src/terminology.js'), 'utf8')
    .replace("import catalog from './terminology.json'", `const catalog = ${JSON.stringify(catalog)}`)
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
}

test('terminology handles singular/plural, capitalization and whole words', async () => {
  const {term, formatTerminology: format, terminologyOptions, normalizeTerminology} = await helpers()
  assert.deepEqual(terminologyOptions('constituency').map(x => x.value), ['constituency', 'district', 'electorate'])
  assert.equal(term('constituency', {}, {plural: true}), 'constituencies')
  for (const [choice, short] of [['constituency', 'const.'], ['district', 'dist.'], ['electorate', 'elect.']]) {
    assert.equal(format('Const. vote score; all as const. seats; CONST.', {constituency: choice}),
      `${short[0].toUpperCase() + short.slice(1)} vote score; all as ${short} seats; ${short.toUpperCase()}`)
  }
  for (const choice of ['district', 'electorate']) {
    assert.equal(format('Constituency votes in all constituencies; CONSTITUENCY', {constituency: choice}),
      `${choice[0].toUpperCase() + choice.slice(1)} votes in all ${choice}s; ${choice.toUpperCase()}`)
    assert.equal(format('constituency_threshold constituenciesCount', {constituency: choice}),
      'constituency_threshold constituenciesCount')
  }
  assert.equal(format('A constituency and a constituency', {constituency: 'electorate'}),
    'An electorate and an electorate')
  assert.equal(format(undefined), undefined)
  assert.deepEqual(normalizeTerminology({constituency: 'invalid'}), {constituency: 'constituency', adjustment_seat: 'adjustment'})
})

test('browser persistence and reactive updates are separate from saved election settings', async () => {
  const {installTerminology, TERMINOLOGY_STORAGE_KEY} = await helpers()
  const {reactive, computed} = require('vue')
  const saved = new Map([[TERMINOLOGY_STORAGE_KEY, '{"constituency":"electorate"}']])
  const storage = {getItem: key => saved.get(key), setItem: (key, value) => saved.set(key, value)}
  const names = ['Northern Constituency', 'Constituency Party', 'Constituency system']
  const state = reactive({terminology: {constituency: 'constituency'}, names})
  let subscriber = () => {}
  const store = {state, subscribe: callback => {subscriber = callback},
    commit(type, payload) {state.terminology = payload; subscriber({type}, state)}}
  const app = {config: {globalProperties: {}}}
  installTerminology(app, store, storage)
  const label = computed(() => app.config.globalProperties.$terms('Constituency disparity'))
  assert.equal(label.value, 'Electorate disparity')
  store.commit('updateTerminology', {constituency: 'district', adjustment_seat: 'top-up'})
  assert.equal(label.value, 'District disparity')
  assert.equal(app.config.globalProperties.$terms('Adjustment seats'), 'Top-up seats')
  assert.deepEqual(JSON.parse(saved.get(TERMINOLOGY_STORAGE_KEY)), {constituency: 'district', adjustment_seat: 'top-up'})
  assert.deepEqual(state.names, names)
  const source = fs.readFileSync(path.join(__dirname, '../src/store.js'), 'utf8')
  assert.doesNotMatch(source.split('async saveAll(')[1].split('calculate_results(')[0], /terminology/)
  assert.doesNotMatch(source.split('uploadAll:')[1].split('async saveAll(')[0], /updateTerminology/)
})

test('blocked or malformed browser storage does not prevent selection', async () => {
  const {installTerminology} = await helpers()
  for (const storage of [
    {getItem() {throw Error('blocked')}, setItem() {throw Error('blocked')}},
    {getItem() {return '{invalid'}, setItem() {}},
  ]) {
    let listener
    const store = {state: {terminology: {constituency: 'constituency'}},
      commit() {}, subscribe(callback) {listener = callback}}
    const app = {config: {globalProperties: {}}}
    assert.doesNotThrow(() => installTerminology(app, store, storage))
    store.state.terminology = {constituency: 'district'}
    assert.doesNotThrow(() => listener({type: 'updateTerminology'}, store.state))
    assert.equal(app.config.globalProperties.$terms('Constituencies'), 'Districts')
  }
})


test('all five adjustment-seat terms support compounds, short headings and articles', async () => {
  const {formatTerminology: format, terminologyOptions} = await helpers()
  const choices = ['adjustment', 'compensatory', 'equalisation', 'levelling', 'top-up']
  assert.deepEqual(terminologyOptions('adjustment_seat').map(x => x.value), choices)
  for (const [index, choice] of choices.entries()) {
    const preferences = {constituency: 'electorate', adjustment_seat: choice}
    const label = choice === 'equalisation' ? 'equalization' : choice
    const article = ['adjustment', 'equalisation'].includes(choice) ? 'an' : 'a'
    const short = ['Adj.', 'Comp.', 'Equal.', 'Lev.', 'Top-up'][index]
    assert.equal(format('An adjustment seat in a constituency', preferences),
      `${article[0].toUpperCase() + article.slice(1)} ${label} seat in an electorate`)
    assert.equal(format('Adjustment seats; ADJUSTMENT SEATS', preferences),
      `${label[0].toUpperCase() + label.slice(1)} seats; ${label.toUpperCase()} SEATS`)
    assert.equal(format('adjustment-seat counts and fixed + adjustment seats', preferences),
      `${label}-seat counts and fixed + ${label} seats`)
    assert.equal(format('# Adj. / # Min adj. / # Max adj.', preferences),
      `# ${short} / # Min ${short.toLowerCase()} / # Max ${short.toLowerCase()}`)
    assert.equal(format('adjustment_method num_adj_seats adjacent', preferences),
      'adjustment_method num_adj_seats adjacent')
  }
})

test('step-by-step explanations translate without altering user names', async () => {
  const {formatTerminology} = await helpers()
  const source = fs.readFileSync(path.join(__dirname, '../src/components/ResultDemonstration.vue'), 'utf8')
    .split('<script>')[1].split('</script>')[0]
    .replace(/^import .*$/gm, '').replace('export default', 'return')
  const component = new Function('mapState', source)(() => ({}))
  const context = {
    table: {headers: ['Constituency', 'Party', 'Criteria'], format: ['l', 'l', 'l']},
    $terms: text => formatTerminology(text, {constituency: 'district', adjustment_seat: 'levelling'}),
  }
  assert.equal(component.methods.format.call(context, 'Const. North', 0), 'Const. North')
  assert.equal(component.methods.format.call(context, 'Adj. Party', 1), 'Adj. Party')
  assert.equal(component.methods.format.call(context, 'No const. seat', 2), 'No dist. seat')
})
