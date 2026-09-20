const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {runInNewContext} = require('node:vm')
const {parse, compileScript} = require('@vue/compiler-sfc')

const source = readFileSync(resolve(__dirname, '../src/ElectoralSystems.vue'), 'utf8')
const storeSource = readFileSync(resolve(__dirname, '../src/store.js'), 'utf8')
const {descriptor} = parse(source)
const script = compileScript(descriptor, {id: 'tabs-test'})
const component = script.scriptAst.find(node => node.type === 'ExportDefaultDeclaration')
const computed = component.declaration.properties.find(node => node.key?.name === 'computed')
const property = computed.value.properties.find(node => node.key?.name === 'activeTabIndex')
const {activeTabIndex} = runInNewContext(
  `({${descriptor.script.content.slice(property.start, property.end)}})`,
)
const nameErrorProperty = computed.value.properties.find(
  node => node.key?.name === 'systemNameError',
)
const {systemNameError} = runInNewContext(
  `({${descriptor.script.content.slice(nameErrorProperty.start, nameErrorProperty.end)}})`,
)
const numberingStart = storeSource.indexOf('function findNumbering')
const numberingEnd = storeSource.indexOf('\n}\n\nfunction error', numberingStart) + 2
const findNumbering = runInNewContext(
  `(${storeSource.slice(numberingStart, numberingEnd)})`,
)

test('the active tab follows a system when move arrows are inserted', () => {
  assert.equal(activeTabIndex.get.call({
    activeSystemIndex: 0,
    system_numbering: [-3, 0, -1, 1, 2],
  }), 1)
  assert.equal(activeTabIndex.get.call({
    activeSystemIndex: 1,
    system_numbering: [0, -2, -3, 1, -1, 2],
  }), 3)
  assert.equal(activeTabIndex.get.call({
    activeSystemIndex: 2,
    system_numbering: [0, 1, -2, -3, 2],
  }), 4)
})

test('the tab control is rebuilt after selection or deletion changes its structure', () => {
  assert.match(descriptor.template.content,
    /:key="`\$\{systems\.length\}:\$\{activeSystemIndex\}`"/)
  assert.match(descriptor.template.content,
    /<b-tab[^>]+@click="handleTabClick\(sysidx\)"/)
})

test('one delete control follows the active system tab', () => {
  const state = {systems: [{}, {}, {}]}
  findNumbering(state, 1)
  assert.deepEqual(Array.from(state.system_numbering), [0, -2, -3, 1, -1, 2])
  assert.equal(state.system_numbering.filter(value => value === -3).length, 1)

  state.systems.splice(1, 1)
  findNumbering(state, 1)
  assert.deepEqual(Array.from(state.system_numbering), [0, -2, -3, 1])
})

test('blank and duplicate electoral system names are reported', () => {
  assert.equal(systemNameError.call({systems: [{name: 'System-1'}, {name: '   '}]}),
    'Electoral system names cannot be blank')
  assert.equal(systemNameError.call({systems: [{name: 'Same'}, {name: 'Same'}]}),
    'All system names should be unique')
  assert.equal(systemNameError.call({systems: [{name: 'System-1'}]}), '')
})
