const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {runInNewContext} = require('node:vm')
const {parse, compileScript, compileTemplate} = require('@vue/compiler-sfc')

const filename = resolve(__dirname, '../src/Main.vue')
const {descriptor} = parse(readFileSync(filename, 'utf8'))
const script = compileScript(descriptor, {id: 'upload-location-test'})
const component = script.scriptAst.find(node => node.type === 'ExportDefaultDeclaration')
const methods = component.declaration.properties.find(node => node.key?.name === 'methods')
function uploadMethods(chooseOpenLocation) {
  const source = methods.value.properties.filter(node => ['chooseAllFile', 'loadAll'].includes(node.key?.name))
    .map(node => descriptor.script.content.slice(node.start, node.end)).join(',')
  return runInNewContext(`({${source}})`, {chooseOpenLocation,
    FormData: class { append(...args) { this.file = args } }})
}

test('native upload passes the source handle through to the store', async () => {
  const file = {name: 'experiment.json'}
  const previous = {name: 'old.json'}
  const handle = {getFile: async () => file}
  let request
  let hidden = false
  const context = {...uploadMethods(async start => {
    assert.equal(start, previous)
    return handle
  }), all_file_handle: previous, allUploadFile: file,
  $refs: {uploadAllDialog: {hide() { hidden = true }}},
  uploadAll(value) { request = value }, serverError: assert.fail}
  await context.chooseAllFile()
  assert.equal(request.filename, file.name)
  assert.equal(request.fileHandle, handle)
  assert.equal(request.formData.file[1], file)
  assert.equal(hidden, true)
  assert.equal(context.allUploadFile, null)
  const {errors} = compileTemplate({source: descriptor.template.content, filename, id: 'upload-location-test'})
  assert.deepEqual(errors, [])
})

test('cancelling the native chooser leaves the current file untouched', async () => {
  const context = {...uploadMethods(async () => { throw {name: 'AbortError'} }),
    uploadAll: assert.fail, serverError: assert.fail}
  await context.chooseAllFile()
})

test('fallback upload supplies the filename without a source handle', () => {
  const file = {name: 'fallback.json'}
  let request
  const context = {...uploadMethods(), $refs: {uploadAllDialog: {hide() {}}},
    uploadAll(value) { request = value }}
  context.loadAll(file)
  assert.equal(request.filename, file.name)
  assert.equal(request.fileHandle, null)
})
