const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")
const test = require("node:test")

const source = fs.readFileSync(
  path.join(__dirname, "../src/Simulate.vue"), "utf8")

test("web simulation results omit detailed seat-allocation matrices", () => {
  assert.doesNotMatch(source, /SimResultMatrix/)
  assert.doesNotMatch(source, /<h4[^>]*>Fixed seats<\/h4>/)
  assert.doesNotMatch(source, /<h4[^>]*>Adjustment seats<\/h4>/)
  assert.doesNotMatch(source, /<h4[^>]*>Total seats<\/h4>/)
})

test("quality-measure blocks can select their displayed statistics", () => {
  const qualitySource = fs.readFileSync(
    path.join(__dirname, "../src/components/QualityMeasures.vue"), "utf8")

  assert.match(qualitySource, /statsForGroup\(id\)/)
  assert.match(qualitySource, /vuedata\.group_stats/)
})
