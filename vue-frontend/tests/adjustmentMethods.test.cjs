const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

async function helpers() {
  const source = readFileSync(resolve(__dirname, '../src/adjustmentMethods.js'), 'utf8')
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
}

// Use the backend catalogue to catch accidental omissions as methods are added.
const dictionary = readFileSync(resolve(__dirname, '../../backend/dictionaries.py'), 'utf8')
const catalogue = dictionary.split('ADJUSTMENT_METHOD_NAMES = [')[1].split('\n]')[0]
const options = [...catalogue.matchAll(/^\s*\{"value": "([^"]+)",\s*"text": "([^"]+)"\}/gm)]
  .map(([, value, text]) => ({value, text}))

async function settingsContext() {
  const helper = await helpers()
  const filename = resolve(__dirname, '../src/ElectionSettings.vue')
  const {descriptor} = parse(readFileSync(filename, 'utf8'))
  const {errors} = compileTemplate({source: descriptor.template.content, filename, id: 'staged-method-test'})
  assert.deepEqual(errors, [])
  const script = descriptor.script.content.replace(/^import[\s\S]*?;/gm, '')
    .replace('export default', 'return')
  const component = new Function('mapState', 'mapMutations', 'mapActions', ...Object.keys(helper), script)(
    () => ({}), () => ({}), () => ({}), ...Object.values(helper))
  const context = {systems: [{adjustment_method: 'icelandic-law'}, {adjustment_method: 'rsss-minl2-double'}],
    systemidx: 0, adjustmentMethodOptions: options}
  for (const name of ['adjustmentFamily', 'adjustmentChoice', 'adjustmentScaling',
    'adjustmentFamilyOptions', 'stagedAdjustmentMethodOptions', 'adjustmentScalingOptions']) {
    const definition = component.computed[name]
    Object.defineProperty(context, name, {
      get: () => (definition.get || definition).call(context),
      set: definition.set && (value => definition.set.call(context, value)),
    })
  }
  return context
}

test('every offered method stays reachable in exactly one family', async () => {
  const h = await helpers()
  for (const option of options) {
    const family = h.methodFamily(option.value)
    const choices = h.methodOptions(options, family)
    const choice = h.methodChoice(option.value)
    assert.ok(choices.some(item => item.value === choice))
    assert.equal(h.selectMethod(options, choice, option.value), option.value)
  }
  assert.equal(h.methodFamily('switching'), 'other')
  assert.equal(h.methodFamily('alternating-scaling'), 'other')
  assert.equal(h.methodFamily('switching-flex'), 'approximation')
  assert.equal(h.methodFamily('max-absolute-margin'), 'single')
  assert.equal(h.methodFamily('norwegian-law'), 'country')
  assert.equal(h.methodFamily('optimal-exact-parties'), 'optimal')
  assert.equal(h.methodFamily('optimal-one-way'), 'optimal')
})

test('every method has help and family overviews put each description on its own line', async () => {
  const h = await helpers()
  for (const option of options) assert.ok(h.methodHelp(option.value).length > 40, option.value)
  for (const family of h.methodFamilies) {
    const choices = h.methodOptions(options, family.value)
    const lines = h.methodOverview(options, family.value).split('\n')
    assert.equal(lines.length, choices.length)
    choices.forEach((choice, i) => assert.ok(lines[i].startsWith(`${choice.text}: `)))
  }
  assert.match(h.methodOverview(options, 'optimal'), /MinL1: Minimize/)
  assert.match(h.methodOverview(options, 'approximation'), /MinL1 switching: Reduce/)
  assert.match(h.methodHelp('adjustment-as-fixed'), /does not enforce/)
  assert.match(h.methodHelp('party-seats-unbounded'), /do not restrict/)
  assert.match(h.allocationRuleHelp('seat-share-switching'), /\nSainte-Laguë:.*\nD’Hondt:.*\nDanish:/)
  assert.doesNotMatch(h.allocationRuleHelp('icelandic-law'), /Minimize|sum s²/)
  const css = readFileSync(resolve(__dirname, '../static/css/app.css'), 'utf8')
  assert.match(css, /\.tooltip\.allocation-help \.tooltip-inner\s*\{\s*white-space: pre-line/)
})

test('RSSS offers two methods and separate scaling, preserving scaling between objectives', async () => {
  const h = await helpers()
  const choices = h.methodOptions(options, 'optimal').filter(option => option.value.startsWith('rsss-'))
  assert.deepEqual(choices.map(option => option.text), ['MinL1', 'MinL2'])
  assert.equal(h.selectMethod(options, 'rsss-minl2', 'rsss-minl1-double'), 'rsss-minl2-double')
  assert.equal(h.selectMethod(options, 'rsss-minl1', 'optimal-lp'), 'rsss-minl1-const')
})

test('disabled methods remain disabled at every stage', async () => {
  const h = await helpers()
  const disabled = options.map(option => ({...option, disabled: option.value !== 'switching-flex'}))
  assert.equal(h.familyOptions(disabled).filter(option => !option.disabled)[0].value, 'approximation')
  assert.ok(h.methodOptions(disabled, 'optimal').every(option => option.disabled))
  assert.ok(h.scalingOptions(disabled, 'rsss-minl1').every(option => option.disabled))
  assert.equal(h.selectMethod(disabled, 'rsss-minl1', 'switching-flex'), 'switching-flex')
})

test('approximation family has four objectives, no Switching+, and RSSS scaling', async () => {
  const h = await helpers()
  assert.deepEqual(h.methodOptions(options, 'approximation').map(option => option.text),
    ['Entropy switching', 'MinL1 switching', 'MinL2 switching', 'Seat-share switching'])
  assert.ok(!options.some(option => option.value === 'switching-plus'))
  const context = await settingsContext()
  context.adjustmentFamily = 'approximation'
  assert.equal(context.adjustmentChoice, 'switching-flex')
  context.adjustmentChoice = 'rsss-minl1-switching'
  context.adjustmentScaling = 'double'
  context.adjustmentChoice = 'rsss-minl2-switching'
  assert.equal(context.systems[0].adjustment_method, 'rsss-minl2-switching-double')
  assert.equal(context.adjustmentScaling, 'double')
  context.adjustmentChoice = 'seat-share-switching'
  assert.equal(context.adjustmentScaling, null)
})

test('real controls round-trip saved methods and follow system and preset changes', async () => {
  const context = await settingsContext()
  assert.equal(context.adjustmentFamily, 'country')
  context.adjustmentFamily = 'optimal'
  assert.equal(context.systems[0].adjustment_method, 'optimal-lp')
  context.adjustmentChoice = 'rsss-minl1'
  context.adjustmentScaling = 'double'
  assert.equal(context.systems[0].adjustment_method, 'rsss-minl1-double')
  context.adjustmentChoice = 'rsss-minl2'
  assert.equal(context.systems[0].adjustment_method, 'rsss-minl2-double')
  context.systemidx = 1
  assert.equal(context.adjustmentChoice, 'rsss-minl2')
  assert.equal(context.adjustmentScaling, 'double')
  // Presets/upload replace the stored identifier; no UI state needs synchronizing.
  context.systems[1] = {adjustment_method: 'norwegian-law'}
  assert.equal(context.adjustmentFamily, 'country')
  assert.equal(context.adjustmentChoice, 'norwegian-law')
  assert.equal(context.adjustmentScaling, null)
  assert.deepEqual(Object.keys(context.systems[1]), ['adjustment_method'])
})
