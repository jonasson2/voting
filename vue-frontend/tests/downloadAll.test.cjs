const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const {runInNewContext} = require('node:vm')
const {parse, compileScript} = require('@vue/compiler-sfc')

const source = readFileSync(resolve(__dirname, '../src/store.js'), 'utf8')
  .replace(/^import .*\n/gm, '')
  .replace('export default store', 'store')

function downloadStore({response, writeError} = {}) {
  const writes = []
  const downloads = []
  const store = runInNewContext(source, {
    Vuex: {Store: class { constructor(options) { Object.assign(this, options) } }},
    defaultDisplaySettings: () => ({}),
    axios: () => Promise.resolve(response || {
      status: 200, data: '{}',
      headers: {'content-type': 'application/octet-stream',
        'content-disposition': 'attachment; filename=server-default.json'},
    }),
    Blob, TextDecoder,
    writeDownload: async (handle, blob) => {
      if (writeError) throw writeError
      writes.push({handle, blob})
    },
    document: {
      createElement: () => ({
        dispatchEvent() { downloads.push(this.download) }, remove() {},
      }),
      body: {appendChild() {}},
    },
    URL: {createObjectURL: () => 'blob:test'},
    MouseEvent: class {},
    window: {setTimeout() {}},
  })
  const commits = []
  const context = {
    state: store.state,
    commit(name, value) {
      commits.push({name, value})
      if (name === 'setAllFile') store.mutations[name](store.state, value)
    },
    dispatch(name, request) { return store.actions[name](context, request) },
  }
  return {store, context, commits, writes, downloads}
}

test('download all remembers the actual saved name and file handle', async () => {
  const {store, context, writes} = downloadStore()
  const first = {name: 'first.json'}
  await store.actions.saveAll(context, {fileHandle: first})
  assert.equal(context.state.all_filename, 'first.json')
  assert.equal(context.state.all_file_handle, first)
  const renamed = {name: 'renamed.json'}
  await store.actions.saveAll(context, {fileHandle: renamed})
  assert.equal(context.state.all_filename, 'renamed.json')
  assert.equal(context.state.all_file_handle, renamed)
  assert.equal(writes.length, 2)
})

test('browser-managed download remembers its requested name', async () => {
  const {store, context, downloads} = downloadStore()
  await store.actions.saveAll(context, {filename: 'experiment.json'})
  assert.equal(context.state.all_filename, 'experiment.json')
  assert.equal(context.state.all_file_handle, null)
  assert.deepEqual(downloads, ['experiment.json'])
})

test('failed saves preserve the previous default and unsaved-change warning', async () => {
  for (const failure of [
    {writeError: new Error('Disk full')},
    {response: {status: 500, body: 'Failed'}},
    {response: {status: 200, headers: {'content-type': 'application/json'},
      data: new TextEncoder().encode('{"error":"Invalid data"}')}},
  ]) {
    const {store, context, commits} = downloadStore(failure)
    const old = {name: 'previous.json'}
    context.commit('setAllFile', {filename: old.name, fileHandle: old})
    await store.actions.saveAll(context, {fileHandle: {name: 'failed.json'}})
    assert.equal(context.state.all_filename, old.name)
    assert.equal(context.state.all_file_handle, old)
    assert.equal(commits.some(item => item.name === 'removeBeforeunload'), false)
    assert.equal(commits.some(item => item.name === 'serverError'), true)
  }
})

test('uploading another file clears the old save location', () => {
  const {store, context} = downloadStore()
  context.commit('setAllFile', {filename: 'old.json', fileHandle: {name: 'old.json'}})
  store.mutations.setAllFile(context.state, {filename: 'uploaded.json'})
  assert.equal(context.state.all_filename, 'uploaded.json')
  assert.equal(context.state.all_file_handle, null)
})

test('both Download all buttons suggest the last saved name and location', async () => {
  for (const file of ['VoteMatrix.vue', 'ElectoralSystems.vue']) {
    const {descriptor} = parse(readFileSync(resolve(__dirname, '../src', file), 'utf8'))
    const script = compileScript(descriptor, {id: 'download-all-test'})
    const component = script.scriptAst.find(node => node.type === 'ExportDefaultDeclaration')
    const methods = component.declaration.properties.find(node => node.key?.name === 'methods')
    const handler = methods.value.properties.find(node => node.key?.name === 'openDownload')
    const previous = {name: 'saved.json'}
    const chosen = {name: 'renamed.json'}
    const {openDownload} = runInNewContext(
      `({${descriptor.script.content.slice(handler.start, handler.end)}})`, {
        canChooseSaveLocation: () => true,
        validDownloadBasename: () => true,
        downloadBasename: name => name.replace(/\.json$/, ''),
        chooseSaveLocation: async (name, extension, handle) => {
          assert.equal(name, 'saved')
          assert.equal(extension, 'json')
          assert.equal(handle, previous)
          return chosen
        },
      })
    let confirmed = false
    await openDownload.call({
      all_filename: previous.name, all_file_handle: previous,
      confirmDownload(destination) {
        assert.equal(destination.fileHandle, chosen)
        confirmed = true
      },
    }, 'all')
    assert.equal(confirmed, true)
  }
})
