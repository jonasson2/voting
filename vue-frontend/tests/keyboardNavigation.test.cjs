const assert = require('node:assert/strict')
const {readFile} = require('node:fs/promises')
const {resolve} = require('node:path')
const {test} = require('node:test')

async function navigationModule() {
  const source = await readFile(resolve(__dirname, '../src/keyboardNavigation.js'), 'utf8')
  return import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
}

test('arrow keys and Enter resolve adjacent grid positions', async () => {
  const {nextGridPosition} = await navigationModule()
  assert.deepEqual(nextGridPosition('ArrowLeft', 1, 1), {row: 1, column: 0})
  assert.deepEqual(nextGridPosition('ArrowRight', 1, 1), {row: 1, column: 2})
  assert.deepEqual(nextGridPosition('ArrowUp', 1, 1), {row: 0, column: 1})
  assert.deepEqual(nextGridPosition('ArrowDown', 1, 1), {row: 2, column: 1})
  assert.deepEqual(nextGridPosition('Enter', 1, 1), {row: 2, column: 1})
  assert.equal(nextGridPosition('Tab', 1, 1), null)
})
