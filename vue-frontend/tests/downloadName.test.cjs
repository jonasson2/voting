const assert = require("node:assert/strict")
const {readFile} = require("node:fs/promises")
const {resolve} = require("node:path")
const {test} = require("node:test")

async function downloadNameModule() {
  const source = await readFile(resolve(__dirname, "../src/downloadName.js"), "utf8")
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`)
}

test("download names retain Unicode and the required file extension", async () => {
  const {downloadFilename, validDownloadBasename} = await downloadNameModule()
  assert.equal(validDownloadBasename("Ísland 2024"), true)
  assert.equal(downloadFilename(" Ísland 2024 ", "xlsx"), "Ísland 2024.xlsx")
  assert.equal(downloadFilename("votes.XLSX", "xlsx"), "votes.XLSX")
  for (const name of ["", "  ", ".", "..", "a/b", "a\\b", "a:b"]) {
    assert.equal(validDownloadBasename(name), false)
  }
})

test("download-all name keeps the existing timestamp format", async () => {
  const {timestampedDownloadBasename} = await downloadNameModule()
  assert.equal(
    timestampedDownloadBasename("simulator", new Date(2026, 8, 16, 17, 4, 3)),
    "simulator-2026.09.16T17.04.03",
  )
})

test("native save picker receives the suggested name", async () => {
  const {canChooseSaveLocation, chooseSaveLocation} = await downloadNameModule()
  const originalWindow = global.window
  const fileHandle = {}
  let options
  try {
    delete global.window
    assert.equal(canChooseSaveLocation(), false)
    global.window = {
      showSaveFilePicker: async value => {
        options = value
        return fileHandle
      },
    }
    assert.equal(canChooseSaveLocation(), true)
    assert.equal(await chooseSaveLocation("Ísland 2024", "xlsx"), fileHandle)
    assert.deepEqual(options, {suggestedName: "Ísland 2024.xlsx"})
  } finally {
    if (originalWindow === undefined) delete global.window
    else global.window = originalWindow
  }
})

test("selected file handle receives the downloaded data", async () => {
  const {writeDownload} = await downloadNameModule()
  const calls = []
  const blob = new Blob(["saved data"])
  const fileHandle = {
    async createWritable() {
      calls.push("open")
      return {
        async write(value) { calls.push(value) },
        async close() { calls.push("close") },
      }
    },
  }
  await writeDownload(fileHandle, blob)
  assert.deepEqual(calls, ["open", blob, "close"])
})
