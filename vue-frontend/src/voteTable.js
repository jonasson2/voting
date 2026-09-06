export function emptyPartyVoteInfo() {
  return {
    name: "–",
    num_fixed_seats: 0,
    num_adj_seats: 0,
    votes: [],
    specified: false,
    total: 0,
    pruned: 0,
  }
}

export function normalizeVoteTable(table) {
  const constituencyCount = Array.isArray(table.constituencies)
    ? table.constituencies.length
    : 0
  if (!Array.isArray(table.pruned)
      || table.pruned.length !== constituencyCount) {
    table.pruned = Array(constituencyCount).fill(0)
  }
  if (!table.party_vote_info) table.party_vote_info = emptyPartyVoteInfo()
  if (!("pruned" in table.party_vote_info)) table.party_vote_info.pruned = 0
  if (!("specified" in table.party_vote_info)) {
    table.party_vote_info.specified = false
  }
  const validBases = ["totals", "party_vote_info", "average"]
  if (!validBases.includes(table.party_vote_basis)
      || !table.party_vote_info.specified) {
    table.party_vote_basis = "totals"
  }
  return table
}

function sumNumbers(values) {
  return values.reduce((sum, value) => sum + Number(value), 0)
}

export function calculateVoteSums(table) {
  normalizeVoteTable(table)
  const row = table.votes.map(
    (votes, index) => sumNumbers(votes) + Number(table.pruned[index])
  )
  const col = table.parties.map((_, partyIndex) =>
    sumNumbers(table.votes.map(votes => votes[partyIndex]))
  )
  const partyVoteTotal = table.party_vote_info.specified
    ? sumNumbers(table.party_vote_info.votes)
      + Number(table.party_vote_info.pruned)
    : 0
  return {
    row,
    col,
    tot: sumNumbers(row),
    pruned: sumNumbers(table.pruned),
    cseats: sumNumbers(
      table.constituencies.map(constituency => constituency.num_fixed_seats)
    ),
    aseats: sumNumbers(
      table.constituencies.map(constituency => constituency.num_adj_seats)
    ),
    partyVoteTotal,
  }
}

function isNonnegativeInteger(value) {
  return Number.isInteger(value) && value >= 0
}

function isNonblankText(value) {
  return typeof value === "string" && value.trim().length > 0
}

export function validVoteTableLabels(table) {
  return isNonblankText(table.name)
    && Array.isArray(table.parties)
    && table.parties.length > 0
    && table.parties.every(isNonblankText)
    && Array.isArray(table.constituencies)
    && table.constituencies.length > 0
    && table.constituencies.every(constituency =>
      constituency && isNonblankText(constituency.name)
    )
}

export function validConstituencySeats(table) {
  if (!table.constituencies.every(constituency =>
    isNonnegativeInteger(constituency.num_fixed_seats)
    && isNonnegativeInteger(constituency.num_adj_seats))) return false

  if (!("max_total_adj_seats" in table)) return true
  if (!isNonnegativeInteger(table.max_total_adj_seats)) return false
  const minimumTotal = sumNumbers(
    table.constituencies.map(constituency => constituency.num_adj_seats)
  )
  if (table.max_total_adj_seats < minimumTotal) return false

  const maxima = table.constituencies.map(constituency =>
    constituency.max_adj_seats === "" ? null : constituency.max_adj_seats
  )
  if (!maxima.every((maximum, index) =>
    maximum === null
    || (isNonnegativeInteger(maximum)
        && maximum >= table.constituencies[index].num_adj_seats))) return false
  return maxima.some(maximum => maximum === null)
    || table.max_total_adj_seats <= sumNumbers(maxima)
}

export function validVotes(table) {
  return Array.isArray(table.votes)
    && Array.isArray(table.pruned)
    && table.pruned.length === table.constituencies.length
    && table.pruned.every(isNonnegativeInteger)
    && table.votes.length === table.constituencies.length
    && table.votes.every(row =>
      row.length === table.parties.length
      && row.every(isNonnegativeInteger)
    )
}

export function validNationalVotes(table) {
  const info = table.party_vote_info
  if (!info
      || typeof info.name !== "string"
      || !isNonnegativeInteger(info.num_fixed_seats)
      || !isNonnegativeInteger(info.num_adj_seats)
      || !isNonnegativeInteger(info.pruned)) return false
  return !info.specified
    || (isNonblankText(info.name)
        && info.votes.length === table.parties.length
        && info.votes.every(isNonnegativeInteger))
}

export function removeParty(table, index) {
  table.parties.splice(index, 1)
  if (Array.isArray(table.party_names)) table.party_names.splice(index, 1)
  table.votes.forEach(row => row.splice(index, 1))
  if (table.party_vote_info.specified) {
    table.party_vote_info.votes.splice(index, 1)
  }
}

export function addParty(table) {
  table.parties.push("")
  if (Array.isArray(table.party_names)) table.party_names.push("")
  table.votes.forEach(row => row.push(1))
  if (table.party_vote_info.specified) table.party_vote_info.votes.push(1)
}

export function removeConstituency(table, index) {
  table.constituencies.splice(index, 1)
  table.votes.splice(index, 1)
  table.pruned.splice(index, 1)
}

export function addConstituency(table) {
  const constituency = {
    name: "–",
    num_fixed_seats: 1,
    num_adj_seats: 1,
  }
  if ("max_total_adj_seats" in table) {
    constituency.max_adj_seats = 1
    table.max_total_adj_seats = Number(table.max_total_adj_seats) + 1
  }
  table.constituencies.push(constituency)
  table.votes.push(Array(table.parties.length).fill(1))
  table.pruned.push(0)
}

export function pruneSmallParties(table, cutoff) {
  const threshold = Number(cutoff)
  if (!Number.isFinite(threshold) || threshold < 0 || threshold > 100) {
    return {error: "Small party cutoff must be a number from 0 to 100"}
  }
  if (!validVotes(table)) {
    return {error: "Constituency votes must be non-negative integers before pruning"}
  }
  if (!validNationalVotes(table)) {
    return {error: "The national name, votes, and seats must be valid before pruning"}
  }
  if (!table.parties.length || !table.votes.length) return {changed: false}

  const partyTotals = table.parties.map((_, partyIndex) =>
    sumNumbers(table.votes.map(row => row[partyIndex]))
  )
  const totalVotes = sumNumbers(partyTotals) + sumNumbers(table.pruned)
  if (!Number.isFinite(totalVotes) || totalVotes <= 0) {
    return {error: "Votes must be non-negative integers before pruning"}
  }
  const keep = partyTotals.map(total => total / totalVotes * 100 >= threshold)
  if (!keep.some(Boolean)) {
    return {error: "Small party cutoff would remove all parties"}
  }
  if (keep.every(Boolean)) return {changed: false}

  table.pruned = table.votes.map(
    (row, constituencyIndex) => table.pruned[constituencyIndex]
      + row.reduce(
        (total, votes, partyIndex) => total + (keep[partyIndex] ? 0 : votes),
        0
      )
  )
  table.parties = table.parties.filter((_, index) => keep[index])
  if (Array.isArray(table.party_names)) {
    table.party_names = table.party_names.filter((_, index) => keep[index])
  }
  table.votes = table.votes.map(row =>
    row.filter((_, index) => keep[index])
  )
  if (table.party_vote_info.specified) {
    table.party_vote_info.pruned += table.party_vote_info.votes.reduce(
      (total, votes, index) => total + (keep[index] ? 0 : votes),
      0
    )
    table.party_vote_info.votes = table.party_vote_info.votes.filter(
      (_, index) => keep[index]
    )
  }
  return {changed: true}
}

export function clearVoteTable(table) {
  table.name = ""
  table.constituencies = []
  table.parties = []
  table.votes = []
  table.pruned = []
  delete table.party_names
  delete table.max_total_adj_seats
  table.party_vote_info = emptyPartyVoteInfo()
  table.party_vote_basis = "totals"
}

export function addAdjustmentSeatMaximums(table) {
  table.max_total_adj_seats = sumNumbers(
    table.constituencies.map(constituency => constituency.num_adj_seats)
  )
  table.constituencies.forEach(constituency => {
    constituency.max_adj_seats = constituency.num_adj_seats
  })
}

export function removeAdjustmentSeatMaximums(table) {
  table.constituencies.forEach(constituency => {
    delete constituency.max_adj_seats
  })
  delete table.max_total_adj_seats
}
