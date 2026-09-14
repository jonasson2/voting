const assert = require("node:assert/strict")
const {readFile} = require("node:fs/promises")
const {resolve} = require("node:path")
const {test} = require("node:test")

async function voteTableModule() {
  const source = await readFile(resolve(__dirname, "../src/voteTable.js"), "utf8")
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
  assert.equal(table.regions[0].abbreviation, "H")
  assert.equal(table.constituencies[0].region, "H")
  assert.equal(regionError(table), "")
  renameRegion(table, 0, "Capital")
  assert.equal(table.constituencies[0].region, "Capital")
  addRegion(table)
  assert.match(regionError(table), /no constituencies/)
  const beforeDuplicate = structuredClone(table)
  assert.match(renameRegion(table, 0, "H"), /unique/)
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
  table.constituencies[0].max_adj_seats = null
  table.max_total_adj_seats = 2
  assert.equal(regionError(table), "")
  table.regions[0].num_adj_seats = 3
  assert.match(regionError(table), /sum/)
  table.regions[0].num_adj_seats = 2
  table.constituencies[0].max_adj_seats = 1
  assert.match(regionError(table), /bounds/)
  table.constituencies[0].max_adj_seats = null
  table.constituencies[0].region = "missing"
  assert.match(regionError(table), /listed region/)
  table.party_vote_info.specified = true
  assert.match(regionError(table), /National party votes/)
})
