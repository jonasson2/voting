const assert = require("node:assert/strict")
const {readFile} = require("node:fs/promises")
const {resolve} = require("node:path")
const {test} = require("node:test")

async function autowidthDirective() {
  const source = await readFile(resolve(__dirname, "../src/autowidth.js"), "utf8")
  const url = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
  return (await import(url)).default
}

test("auto-width measures text without DOM mirrors and caches unchanged values", async (t) => {
  let measurements = 0
  global.document = {
    createElement(type) {
      assert.equal(type, "canvas")
      return {
        getContext() {
          return {
            font: "",
            measureText(text) {
              measurements += 1
              return {width: text.length * 10}
            },
          }
        },
      }
    },
  }
  global.window = {
    getComputedStyle() {
      return {font: "12px monospace", letterSpacing: "0px", textTransform: "none"}
    },
  }
  t.after(() => {
    delete global.document
    delete global.window
  })

  const directive = await autowidthDirective()
  const element = {value: "123", placeholder: "", style: {}}
  const binding = {value: {minWidth: "25px", maxWidth: "100px"}}

  directive.mounted(element, binding)
  assert.equal(element.style.width, "32px")
  assert.equal(measurements, 1)

  directive.updated(element, binding)
  assert.equal(measurements, 1)

  element.value = "12345"
  directive.updated(element, binding)
  assert.equal(element.style.width, "52px")
  assert.equal(measurements, 2)
})

test("auto-width restores enough room after formatting an edited integer", async (t) => {
  global.document = {
    createElement() {
      return {getContext() { return {
        font: "",
        measureText(text) { return {width: text.length * 10} },
      } }}
    },
  }
  global.window = {
    getComputedStyle() {
      return {font: "12px monospace", letterSpacing: "0px", textTransform: "none"}
    },
  }
  t.after(() => {
    delete global.document
    delete global.window
  })

  const directive = await autowidthDirective()
  const element = {value: "1,200", placeholder: "", style: {}}
  Object.defineProperties(element, {
    clientWidth: {get() { return Math.round(parseFloat(element.style.width) + 4) }},
    scrollWidth: {get() {
      return Math.max(element.clientWidth, element.value === "1,200" ? 57 : 47)
    }},
  })
  const binding = {value: {minWidth: "25px", maxWidth: "100px"}}

  for (const value of ["1,200", "1200", "1,200", "1200", "1,200"]) {
    element.value = value
    directive.updated(element, binding)
    assert.ok(element.clientWidth >= element.scrollWidth, value)
  }
})
