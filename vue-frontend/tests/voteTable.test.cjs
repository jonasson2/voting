const assert = require("node:assert/strict")
const {readFile} = require("node:fs/promises")
const {resolve} = require("node:path")
const {test} = require("node:test")

async function voteTableModule() {
  const source = await readFile(resolve(__dirname, "../src/voteTable.js"), "utf8")
  const url = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
  return import(url)
}

async function numberFormatModule() {
  const source = await readFile(resolve(__dirname, "../src/numberFormat.js"), "utf8")
  const url = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
  return import(url)
}

function exampleTable() {
  return {
    name: "Example",
    parties: ["A", "B"],
    constituencies: [{
      name: "I",
      num_fixed_seats: 1,
      num_adj_seats: 0,
    }],
    votes: [[90, 10]],
    pruned: [0],
    party_vote_info: {
      name: "National",
      num_fixed_seats: 0,
      num_adj_seats: 0,
      votes: [90, 10],
      specified: true,
      total: 100,
      pruned: 0,
    },
    party_vote_basis: "totals",
  }
}

test("pruning rejects invalid national votes without changing the table", async () => {
  const {pruneSmallParties} = await voteTableModule()
  const table = exampleTable()
  table.party_vote_info.votes[1] = "bad"
  const original = structuredClone(table)

  const result = pruneSmallParties(table, 20)

  assert.match(result.error, /national name, votes, and seats/)
  assert.deepEqual(table, original)
})

test("pruning keeps the largest party in an otherwise empty local contest", async () => {
  const {pruneSmallParties} = await voteTableModule()
  const table = exampleTable()
  table.parties = ["National", "Local runner-up", "Local winner"]
  table.constituencies = [
    {name: "Mainland", num_fixed_seats: 9, num_adj_seats: 0},
    {name: "Island", num_fixed_seats: 1, num_adj_seats: 0},
  ]
  table.votes = [[1000, 0, 0], [0, 40, 60]]
  table.pruned = [0, 0]
  table.party_vote_info.votes = [1000, 40, 60]
  table.party_vote_info.total = 1100

  const result = pruneSmallParties(table, 10)

  assert.deepEqual(result, {changed: true})
  assert.deepEqual(table.parties, ["National", "Local winner"])
  assert.deepEqual(table.votes, [[1000, 0], [0, 60]])
  assert.deepEqual(table.pruned, [0, 40])
})

test("pruning keeps tied largest parties in an otherwise empty local contest", async () => {
  const {pruneSmallParties} = await voteTableModule()
  const table = exampleTable()
  table.parties = ["National", "Local A", "Local B", "Smaller local"]
  table.constituencies = [
    {name: "Mainland", num_fixed_seats: 9, num_adj_seats: 0},
    {name: "Island", num_fixed_seats: 1, num_adj_seats: 0},
  ]
  table.votes = [[1000, 0, 0, 0], [0, 50, 50, 10]]
  table.pruned = [0, 0]
  table.party_vote_info.votes = [1000, 50, 50, 10]
  table.party_vote_info.total = 1110

  const result = pruneSmallParties(table, 10)

  assert.deepEqual(result, {changed: true})
  assert.deepEqual(table.parties, ["National", "Local A", "Local B"])
  assert.deepEqual(table.pruned, [0, 10])
})

test("vote-table labels must be present", async () => {
  const {validVoteTableLabels} = await voteTableModule()
  const table = exampleTable()
  assert.equal(validVoteTableLabels(table), true)

  table.parties[1] = " "
  assert.equal(validVoteTableLabels(table), false)
})

test("a specified national vote row must have a name", async () => {
  const {validNationalVotes} = await voteTableModule()
  const table = exampleTable()
  assert.equal(validNationalVotes(table), true)

  table.party_vote_info.name = ""
  assert.equal(validNationalVotes(table), false)
  table.party_vote_info.name = "National"
  table.party_vote_info.votes[0] = -1
  assert.equal(validNationalVotes(table), false)
})

test("a hyphen represents an unlimited constituency adjustment-seat maximum", async () => {
  const {normalizeVoteTable, validConstituencySeats} = await voteTableModule()
  const table = exampleTable()
  table.max_total_adj_seats = 2
  table.constituencies[0].max_adj_seats = null

  normalizeVoteTable(table)

  assert.equal(table.constituencies[0].max_adj_seats, "-")
  assert.equal(validConstituencySeats(table), true)
  table.constituencies[0].max_adj_seats = 1
  table.constituencies[0].num_adj_seats = 2
  assert.equal(validConstituencySeats(table), false)
  table.constituencies[0].max_adj_seats = ""
  assert.equal(validConstituencySeats(table), false)
})

test("flexible seat pools require compatible adjustment methods", async () => {
  const {
    flexibleAdjustmentMethodOptions,
    hasIncompatibleFlexibleAdjustmentMethod,
  } = await voteTableModule()
  const table = exampleTable()
  table.max_total_adj_seats = 0
  table.constituencies[0].max_adj_seats = 2
  const systems = [{adjustment_method: "fixed-only"}]
  const flexibleMethods = ["flexible"]

  assert.equal(hasIncompatibleFlexibleAdjustmentMethod(
    table, systems, flexibleMethods), false)

  table.max_total_adj_seats = 1
  assert.equal(hasIncompatibleFlexibleAdjustmentMethod(
    table, systems, flexibleMethods), true)

  systems[0].adjustment_method = "flexible"
  assert.equal(hasIncompatibleFlexibleAdjustmentMethod(
    table, systems, flexibleMethods), false)

  const options = [
    {value: "fixed-only", text: "Fixed only"},
    {value: "flexible", text: "Flexible"},
  ]
  assert.deepEqual(
    flexibleAdjustmentMethodOptions(table, options, flexibleMethods),
    [
      {value: "fixed-only", text: "Fixed only", disabled: true},
      {value: "flexible", text: "Flexible", disabled: false},
    ],
  )
  assert.equal("disabled" in options[0], false)
})

test("the maximum-seat column total sums finite maxima and shows unlimited otherwise", async () => {
  const {calculateVoteSums} = await voteTableModule()
  const table = exampleTable()
  table.max_total_adj_seats = 5
  table.constituencies[0].max_adj_seats = 2
  table.constituencies.push({name: "II", num_fixed_seats: 1,
    num_adj_seats: 1, max_adj_seats: 4})
  table.votes.push([10, 20])
  table.pruned.push(0)

  assert.equal(calculateVoteSums(table).maxAdjSeats, 6)
  table.constituencies[1].max_adj_seats = "-"
  assert.equal(calculateVoteSums(table).maxAdjSeats, null)
  table.constituencies[1].max_adj_seats = ""
  assert.equal(calculateVoteSums(table).maxAdjSeats, null)
})

test("constituency votes must be non-negative integers", async () => {
  const {validVotes} = await voteTableModule()
  const table = exampleTable()
  assert.equal(validVotes(table), true)

  table.votes[0][0] = -1

  assert.equal(validVotes(table), false)
})

test("party edits and pruning keep independent flags aligned", async () => {
  const {addParty, removeParty, pruneSmallParties} = await voteTableModule()
  const table = exampleTable()
  table.independent_candidates = [false, true]
  table.party_names = ["Party", "Candidate"]
  addParty(table)
  assert.deepEqual(table.independent_candidates, [false, true, false])
  removeParty(table, 2)
  pruneSmallParties(table, 20)
  assert.deepEqual(table.independent_candidates, [false])
  assert.deepEqual(table.party_names, ["Party"])
  assert.deepEqual(table.pruned, [10])
})

test("region controls retain assignments on rename and remove them on deletion", async () => {
  const {addRegion, renameRegion, removeRegion, regionError} = await voteTableModule()
  const table = exampleTable()
  addRegion(table)
  assert.equal(table.regions, undefined)
  table.party_vote_info.specified = false
  addRegion(table)
  assert.deepEqual(table.regions[0], {abbreviation: "R1", name: "R1", num_adj_seats: 0})
  assert.equal(table.constituencies[0].region, "R1")
  assert.equal(regionError(table), "")
  renameRegion(table, 0, "Capital")
  assert.equal(table.constituencies[0].region, "Capital")
  addRegion(table)
  assert.deepEqual(table.regions[1], {abbreviation: "R2", name: "R2", num_adj_seats: 0})
  assert.match(regionError(table), /no constituencies/)
  const beforeDuplicate = structuredClone(table)
  assert.match(renameRegion(table, 0, "R2"), /unique/)
  assert.deepEqual(table, beforeDuplicate)
  removeRegion(table, 1)
  removeRegion(table, 0)
  assert.equal(table.constituencies[0].region, undefined)
})

test("region validation enforces bounds, totals, identifiers and national-vote exclusion", async () => {
  const {regionError} = await voteTableModule()
  const table = exampleTable()
  table.party_vote_info.specified = false
  table.regions = [{abbreviation: "H", name: "Capital", num_adj_seats: 2}]
  table.constituencies[0].region = "H"
  table.constituencies[0].max_adj_seats = "-"
  table.max_total_adj_seats = 2
  assert.equal(regionError(table), "")
  table.regions[0].num_adj_seats = 3
  assert.match(regionError(table), /sum/)
  table.regions[0].num_adj_seats = 2
  table.constituencies[0].max_adj_seats = 1
  assert.match(regionError(table), /bounds/)
  table.constituencies[0].max_adj_seats = "-"
  table.constituencies[0].region = "missing"
  assert.match(regionError(table), /listed region/)
  table.party_vote_info.specified = true
  assert.match(regionError(table), /National party votes/)
})

test("result numbers use the selected separators and precision", async () => {
  const {
    defaultDisplaySettings,
    formatEstimateWithCi,
    formatNumber,
    formatNumberUnlessZero,
    normalizeDisplaySettings,
    parseInteger,
    validIntegerEntry,
  } = await numberFormatModule()
  assert.equal(defaultDisplaySettings().percentage_digits, 2)
  assert.equal(normalizeDisplaySettings({}).percentage_digits, 2)
  assert.equal(normalizeDisplaySettings({percentage_digits: 4}).percentage_digits, 4)
  assert.equal(normalizeDisplaySettings({percentage_digits: 20}).percentage_digits, 10)
  const voteShare = 100 * 4000 / 7700
  assert.equal(formatNumber(voteShare, defaultDisplaySettings().percentage_digits,
    defaultDisplaySettings()) + "%", "51.95%")
  const fourDigits = normalizeDisplaySettings({percentage_digits: 4})
  assert.equal(formatNumber(voteShare, fourDigits.percentage_digits,
    fourDigits) + "%", "51.9481%")
  assert.equal(formatNumber(12345.6789, 3, {
    thousands_separator: ",",
    decimal_separator: ".",
  }), "12,345.679")
  assert.equal(formatNumber(12345.6789, 2, {
    thousands_separator: ".",
    decimal_separator: ",",
  }), "12.345,68")
  assert.equal(formatNumber(-12345.6, 1, {
    thousands_separator: " ",
    decimal_separator: ",",
  }), "-12\u202f345,6")
  assert.equal(formatNumberUnlessZero(0, 3, {}), "")
  assert.equal(formatNumberUnlessZero(-0, 3, {}), "")
  assert.equal(formatNumberUnlessZero(0.0004, 3, {}), "")
  assert.equal(formatNumberUnlessZero(0.0006, 3, {}), "0.001")
  assert.equal(formatNumberUnlessZero(NaN, 3, {}), "–")
  assert.equal(formatEstimateWithCi(0, 0, 3, {}), "")
  assert.equal(formatEstimateWithCi(1.2344, 0.0004, 3, {}), "1.234 ± 0.000")
  assert.equal(formatEstimateWithCi(0.0004, 0.0014, 3, {}), "0.000 ± 0.001")
  assert.equal(formatEstimateWithCi(1.2344, null, 3, {}), "1.234")
  const comma = {thousands_separator: ",", decimal_separator: "."}
  const dot = {thousands_separator: ".", decimal_separator: ","}
  const space = {thousands_separator: " ", decimal_separator: ","}
  assert.equal(parseInteger("12345", comma), 12345)
  assert.equal(parseInteger("12,345", comma), 12345)
  assert.equal(parseInteger("12.345", dot), 12345)
  assert.equal(parseInteger("12 345", space), 12345)
  assert.equal(parseInteger("12\u00a0345", space), 12345)
  assert.equal(parseInteger("bad", comma), "bad")
  assert.equal(parseInteger("423.122,00", comma), "423.122,00")
  assert.equal(parseInteger("423,122.00", comma), "423,122.00")
  assert.equal(parseInteger("12,34", comma), "12,34")
  assert.equal(parseInteger("1,2345", comma), "1,2345")
  assert.equal(parseInteger("-", comma, true), "-")
  assert.equal(validIntegerEntry("423122", comma), true)
  assert.equal(validIntegerEntry("423,122", comma), true)
  assert.equal(validIntegerEntry("423.122", comma), false)
  assert.equal(validIntegerEntry("423.122,00", comma), false)
  assert.equal(validIntegerEntry("1,2345", comma), false)
  assert.equal(validIntegerEntry("-", comma, true), true)
  assert.equal(validIntegerEntry("-", comma, false), false)
})
