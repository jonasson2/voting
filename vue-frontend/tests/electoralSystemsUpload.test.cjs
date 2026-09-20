const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {runInNewContext} = require('node:vm')
const {parse, compileScript} = require('@vue/compiler-sfc')

const source = readFileSync(resolve(__dirname, '../src/ElectoralSystems.vue'), 'utf8')
const {descriptor} = parse(source)
const script = compileScript(descriptor, {id: 'upload-test'})
const component = script.scriptAst.find(node => node.type === 'ExportDefaultDeclaration')
const methods = component.declaration.properties.find(node => node.key?.name === 'methods')
const handler = methods.value.properties.find(node => node.key?.name === 'uploadSystems')
// Exercise the component's handler without needing a browser or mounting the page.
const {uploadSystems} = runInNewContext(
  `({${descriptor.script.content.slice(handler.start, handler.end)}})`, {FormData})

test('empty file events do not close the dialog or start an upload', () => {
  const context = {
    uploadfile: new Blob(['stale selection']),
    $refs: {modaluploadesettingsref: {hide: () => assert.fail('Unexpected hide')}},
    uploadElectoralSystems: () => assert.fail('Unexpected upload'),
  }
  uploadSystems.call(context, null)
  uploadSystems.call(context, undefined)
})

test('upload uses the selected file event and preserves replace or append mode', () => {
  for (const replace of [true, false]) {
    const calls = []
    const context = {
      uploadfile: null,
      replace,
      $refs: {modaluploadesettingsref: {hide: () => calls.push('hide')}},
      uploadElectoralSystems: payload => calls.push(payload),
    }
    const file = new File(['{}'], 'invalid-settings.json', {type: 'application/json'})
    uploadSystems.call(context, file)
    assert.equal(calls.length, 2)
    assert.equal(calls[0], 'hide')
    assert.equal(calls[1].replace, replace)
    assert.equal(calls[1].formData.get('file').name, file.name)
    assert.equal(calls[1].formData.get('file').size, file.size)
  }
})

test('waiting for an upload does not unmount the modal ancestor', () => {
  const root = descriptor.template.ast.children.find(node => node.tag === 'div')
  assert.equal(root.props.some(prop => prop.name === 'if'), false)
  assert.equal(root.props.find(prop => prop.name === 'show').exp.content,
    'show_systems && !waiting_for_data')
})

test('imported systems are installed unchanged, rather than copied from the preceding system', () => {
  const storeSource = readFileSync(resolve(__dirname, '../src/store.js'), 'utf8')
  const uploadAction = storeSource.slice(
    storeSource.indexOf('uploadElectoralSystems(context, payload)'),
    storeSource.indexOf('uploadAll: function', storeSource.indexOf('uploadElectoralSystems')),
  )
  assert.match(uploadAction, /context\.commit\("updateSystems", systems\)/)
  assert.doesNotMatch(uploadAction, /context\.commit\("addSystem"/)
})
