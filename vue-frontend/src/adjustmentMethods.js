// Presentation only: systems continue to store the existing adjustment_method.
export const methodFamilies = [
  {value: 'country', text: 'Country laws'},
  {value: 'optimal', text: 'Optimal methods'},
  {value: 'approximation', text: 'Approximations to optimal methods'},
  {value: 'single', text: 'Single-seat constituency methods'},
  {value: 'other', text: 'Other exploratory methods'},
]

const families = {
  country: ['max-const-votes', 'norwegian-law', 'icelandic-law'],
  optimal: ['optimal-lp', 'optimal-exact-parties', 'optimal-one-way',
    'seat-share-lp', 'rsss-minl1-const', 'rsss-minl1-double',
    'rsss-minl2-const', 'rsss-minl2-double'],
  approximation: ['switching-flex', 'seat-share-switching',
    'rsss-minl1-switching-const', 'rsss-minl1-switching-double',
    'rsss-minl2-switching-const', 'rsss-minl2-switching-double'],
  single: ['max-relative-margin', 'max-absolute-margin'],
}

export function methodFamily(method) {
  return Object.keys(families).find(family => families[family].includes(method)) || 'other'
}

export function rsssScaling(method) {
  return /^rsss-minl[12]-(?:switching-)?(const|double)$/.exec(method)?.[1] || null
}

export function methodChoice(method) {
  return rsssScaling(method) ? method.replace(/-(const|double)$/, '') : method
}

export function familyOptions(options) {
  return methodFamilies.map(family => ({
    ...family,
    disabled: !options.some(option => methodFamily(option.value) === family.value && !option.disabled),
  }))
}

export function alphabeticalOptions(options) {
  return [...options].sort((a, b) => a.text.localeCompare(b.text, 'en', {numeric: true, sensitivity: 'base'}))
}

export function methodOptions(options, family) {
  const result = []
  for (const option of options.filter(item => methodFamily(item.value) === family)) {
    const value = methodChoice(option.value)
    const existing = result.find(item => item.value === value)
    if (existing) {
      existing.disabled = existing.disabled && !!option.disabled
    } else {
      result.push({...option, value, disabled: !!option.disabled,
        text: rsssScaling(option.value) ? option.text.replace(/ with .* scaling$/, '') : option.text})
    }
  }
  return alphabeticalOptions(result)
}

export function scalingOptions(options, choice) {
  return [
    {value: 'const', text: 'Constituency scaling'},
    {value: 'double', text: 'Double scaling'},
  ].map(option => ({...option,
    disabled: !options.some(item => item.value === `${choice}-${option.value}` && !item.disabled),
  }))
}

export function selectMethod(options, choice, current) {
  const variants = options.filter(option => methodChoice(option.value) === choice && !option.disabled)
  return variants.find(option => rsssScaling(option.value) === rsssScaling(current))?.value
    || variants[0]?.value || current
}

export const allocationFamilyHelp = [
  'Country laws: allocation procedures used in national systems; selecting one does not impose the country’s complete legal seat structure.',
  'Optimal methods: optimize a specified objective subject to the seat constraints.',
  'Approximations to optimal methods: improve an allocation by switching seats; may stop short of the global optimum.',
  'Single-seat constituency methods: compare the leading list’s margin over its nearest rival.',
  'Other exploratory methods: alternative allocation procedures and comparison baselines.',
  '',
  'Methods incompatible with flexible constituency seat counts are disabled.',
].join('\n')

export const allocationScalingHelp = [
  'Constituency scaling: the list’s share of constituency votes times the constituency’s total seats (fixed + adjustment).',
  'Double scaling: scale rows and columns of the vote table to fit constituency and party seat totals.',
  '',
  'These fair shares define the MinL1 or MinL2 allocation objective. This choice is independent of which reference scalings are displayed in simulation results.',
].join('\n')

const pairwiseLimit = 'Stops when no improving pairwise exchange remains. A longer cycle may still improve the allocation.'
const fixedTotals = 'Requires prescribed constituency seat totals. Honour party targets and retain protected fixed seats.'
const seatShareObjective = 'Minimize sum [d(1) + ... + d(s)]/q over lists. Here s is allocated seats, d(k) the selected divisor, and q the constituency-scaled fair share (fractional seat entitlement).'

const methodDescriptions = {
  'max-const-votes': {
    summary: 'Choose the largest available votes/divisor quotient.',
    detail: 'Allocate each adjustment seat to the eligible list with the largest votes/next-divisor quotient, respecting party targets and constituency seat bounds. Used for list placement in Swedish and Danish procedures; their other legal rules are selected separately.',
  },
  'norwegian-law': {
    summary: 'Weight vote-share quotients by fixed constituency seats.',
    detail: 'Allocate each adjustment seat using the largest score: constituency vote share × fixed constituency seats / next divisor. Respect party targets and constituency seat totals. This is the Norwegian weighted quotient (Norwegian law).',
  },
  'icelandic-law': {
    summary: 'Choose the party first, then its best vote-share quotient.',
    detail: 'Take parties in the national adjustment-seat order. For the chosen party, allocate the seat where its constituency vote share divided by its next divisor is highest among constituencies with room. The selected national and list-allocation rules determine the quotients; the Icelandic preset supplies the statutory choices.',
  },
  'optimal-lp': {
    summary: 'Maximize the product of allocated-seat quotients.',
    detail: 'Maximize the product of votes/d(k) over allocated seats, calculated through its logarithm. Honour party targets, protected fixed seats and constituency seat bounds. Supports prescribed or flexible constituency totals. The selected divisor rule defines the objective.',
  },
  'optimal-exact-parties': {
    summary: 'Maximize the quotient product with exactly represented parties intact.',
    detail: 'First retain fixed seats and fill the remaining seats independently within each constituency using the selected divisor rule, ignoring national party targets. Preserve every list allocation of parties whose resulting totals equal their prescribed targets.\nThen maximize the product of allocated-seat quotients votes/divisor for the remaining parties using a network LP.\nRequires prescribed constituency and party totals; retains all original fixed seats.',
  },
  'optimal-one-way': {
    summary: 'Maximize the quotient product allowing only one-way constituency corrections.',
    detail: 'First retain fixed seats and fill the remaining seats independently within each constituency using the selected divisor rule, ignoring national party targets. Keep exactly represented parties intact. Initially overrepresented parties may only lose seats from their lists; initially underrepresented parties may only gain seats.\nMaximize the product of allocated-seat quotients votes/divisor subject to these restrictions using a network LP.\nRequires prescribed constituency and party totals; retains all original fixed seats.',
  },
  'seat-share-lp': {
    summary: 'Minimize cumulative divisor costs divided by fair shares.',
    detail: `${seatShareObjective}\nFind the minimum using a network LP. With Sainte-Laguë this is sum s²/q, equivalent to minimizing sum (s-q)²/q.\n${fixedTotals}`,
  },
  'rsss-minl1': {
    summary: 'Minimize total absolute list seat deviation.',
    detail: `Minimize sum abs(s-q), where s is allocated seats and q is the fair share from the selected scaling. Find the minimum using a network LP.\n${fixedTotals}\nNo adjustment-seat divisor rule or extra constituency weights are used.`,
  },
  'rsss-minl2': {
    summary: 'Minimize total squared list seat deviation.',
    detail: `Minimize sum (s-q)², where s is allocated seats and q is the fair share from the selected scaling. Find the minimum using a network LP.\n${fixedTotals}\nNo adjustment-seat divisor rule or extra constituency weights are used.`,
  },
  'switching-flex': {
    summary: 'Increase the product of allocated-seat quotients.',
    detail: 'Start from a feasible allocation by votes/next-divisor quotients. Repeatedly choose the pairwise exchange or permitted seat move giving the largest increase in the log quotient product. Preserve fixed seats and party totals; constituency totals may be prescribed or flexible.\nStop when no such exchange or move improves the objective. Longer cycles may still improve it.',
  },
  'seat-share-switching': {
    summary: 'Reduce the same objective as Seat-share optimization.',
    detail: `${seatShareObjective}\nStart from fair-share/divisor quotients and repeatedly choose the pairwise exchange giving the largest cost reduction.\n${pairwiseLimit}\n${fixedTotals}`,
  },
  'rsss-minl1-switching': {
    summary: 'Reduce total absolute list seat deviation.',
    detail: `Reduce sum abs(s-q), using the same fair shares and objective as exact MinL1. Start from a feasible allocation and repeatedly choose the pairwise exchange giving the greatest reduction.\n${pairwiseLimit}\n${fixedTotals}\nNo adjustment-seat divisor rule or extra constituency weights are used.`,
  },
  'rsss-minl2-switching': {
    summary: 'Reduce total squared list seat deviation.',
    detail: `Reduce sum (s-q)², using the same fair shares and objective as exact MinL2. Start from a feasible allocation and repeatedly choose the pairwise exchange giving the greatest reduction.\n${pairwiseLimit}\n${fixedTotals}\nNo adjustment-seat divisor rule or extra constituency weights are used.`,
  },
  'max-absolute-margin': {
    summary: 'Choose the largest difference between the top two quotients.',
    detail: 'In each constituency, compare the two highest next-seat quotients among eligible parties. Allocate to the leading list in the constituency with the largest difference. Intended for comparing single-seat constituency allocations; it still respects party targets.',
  },
  'max-relative-margin': {
    summary: 'Choose the largest ratio between the top two quotients.',
    detail: 'In each constituency, compare the two highest next-seat quotients among eligible parties. Allocate to the leading list in the constituency with the largest ratio. Intended for comparing single-seat constituency allocations; it still respects party targets.',
  },
  'adjustment-as-fixed': {
    summary: 'Allocate independently within constituencies.',
    detail: 'Allocate adjustment seats as further fixed seats within each constituency using the selected divisor rule. This comparison baseline does not enforce the national party targets.',
  },
  'alternating-scaling': {
    summary: 'Alternate constituency and party scaling.',
    detail: 'Iteratively rescale votes and apply divisor allocations to try to satisfy constituency and party totals. This historical implementation is not a guarantee of the optimum found by Biproportional rounding.',
  },
  'ice-shares': {
    summary: 'Use Icelandic party order with fair-share quotients.',
    detail: 'Take parties in the national adjustment-seat order, as in the Icelandic procedure. Place each seat using fair share/next divisor instead of vote share/next divisor. This is a hypothetical variant, not Icelandic law.',
  },
  'max-const-seat-share': {
    summary: 'Choose the largest fair-share/divisor quotient.',
    detail: 'Allocate the next adjustment seat to the eligible list with the largest fair share (fractional seat entitlement) divided by its next divisor.',
  },
  'max-const-vote-percentage': {
    summary: 'Choose the largest vote-share/divisor quotient.',
    detail: 'Allocate each adjustment seat to the eligible list with the largest constituency vote share divided by its next divisor. Respect party targets and constituency seat bounds.',
  },
  'party-seats-unbounded': {
    summary: 'Use fair-share quotients without enforcing party targets.',
    detail: 'Allocate seats using the largest fair-share/next-divisor quotient while filling the prescribed constituency totals. National party targets do not restrict recipients.',
  },
  'relative-superiority': {
    summary: 'Compare the next quotient with a replacement allocation.',
    detail: 'For each constituency, compare the leading next-seat quotient with a substitute quotient obtained by provisionally filling its remaining seats without that party. The look-ahead limits other parties by their targets. Allocate where this ratio is greatest.',
  },
  'relative-sup-simple': {
    summary: 'Use a simplified look-ahead quotient comparison.',
    detail: 'Compare the leading next-seat quotient with a substitute quotient from a provisional allocation that can include further seats for the same party and does not cap the look-ahead by party targets. Actual allocations still respect the targets. Supports a flexible seat pool.',
  },
  'switching': {
    summary: 'Transfer seats from surplus parties to deficit parties.',
    detail: 'First allocate within each constituency as if all seats were fixed. Then transfer seats within constituencies from parties above their targets to parties below them, choosing by the ratio of outgoing to incoming quotients. Stop once the party targets are satisfied; there is no further entropy-improvement stage. Protected fixed seats remain in place.',
  },
  'swedish-style-switching': {
    summary: 'Remove excess seats, then reassign the vacancies.',
    detail: 'Start from provisional constituency allocations. Remove the weakest removable seats of parties above their targets, then reassign vacancies by next-seat quotients to parties with deficits. Supports fixed or flexible constituency totals and retains protected fixed seats. This adjustment-seat method is separate from the Swedish special rules.',
  },
}

export function methodHelp(method) {
  const description = methodDescriptions[methodChoice(method)]?.detail || ''
  return description && rsssScaling(method) && !method.includes('-switching-')
    ? `${description}\n\nRicca et al. (2012).`
    : description
}

export function methodOverview(options, family) {
  return methodOptions(options, family).map(option =>
    `${option.text}: ${methodDescriptions[option.value]?.summary || ''}`).join('\n')
}

export function allocationRuleHelp(method) {
  const general = 'Choose the divisor sequence used by this list-allocation method. The rules for fixed seats and total party entitlements are selected separately.'
  if (method.startsWith('seat-share-')) {
    return [general, '', seatShareObjective,
      'Sainte-Laguë: sum s²/q.',
      'D’Hondt: sum s(s+1)/(2q).',
      'Danish: sum s(3s−1)/(2q).',
      'Other rules: sum [d(1) + ... + d(s)]/q.',
      '', 'Exact and switching versions use the same objective.'].join('\n')
  }
  return `${general}\n\nEach list’s next quotient uses its next divisor, counting both fixed and adjustment seats already allocated. For entropy methods the objective is the product of allocated-seat quotients votes/d(k); other methods may weight or compare quotients as described in their tooltips.`
}
