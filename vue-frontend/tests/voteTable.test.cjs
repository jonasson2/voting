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
