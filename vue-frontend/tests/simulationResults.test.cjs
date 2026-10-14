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
  assert.doesNotMatch(source, />Quality measures<\/span>/)
})

test("quality-measure blocks can select their displayed statistics", () => {
  const qualitySource = fs.readFileSync(
    path.join(__dirname, "../src/components/QualityMeasures.vue"), "utf8")

  assert.match(qualitySource, /statsForGroup\(id\)/)
  assert.match(qualitySource, /vuedata\.group_stats/)
})

test("optional rows toggle without rerunning, with section titles in their own column", async () => {
  const Vue = require('vue')
  const {renderToString} = require('@vue/server-renderer')
  const {parse, compileTemplate} = require('@vue/compiler-sfc')
  const filename = path.join(__dirname, '../src/components/QualityMeasures.vue')
  const {descriptor} = parse(fs.readFileSync(filename, 'utf8'))
  const {code, errors} = compileTemplate({source: descriptor.template.content,
    filename, id: 'quality-measures-test', compilerOptions: {mode: 'function'}})
  assert.deepEqual(errors, [])
  const {formatNumber} = await import('../src/numberFormat.js')
  const settings = {show_additional: false, show_scalings: false, show_single_seat: false}
  const script = descriptor.script.content.replace(/^import .*$/gm, '')
    .replace('export default', 'return')
  const component = new Function('mapState', 'formatNumber', script)(
    () => ({display_settings: () => ({fractional_digits: 3, percentage_digits: 1}),
      sim_settings: () => settings}), formatNumber)
  component.render = new Function('Vue', code)(Vue)
  const row = (rowtitle, option) => ({rowtitle, option,
    avg: [{value: 0.125, ci: 0.01}], std: [{value: 0.05, ci: null}]})
  const vuedata = {
    stats: ['avg', 'std'], stat_headings: {avg: 'Average & 95% confidence interval', std: 'STD.DEV.'},
    system_names: ['System A'], group_ids: ['const', 'singleSeat', 'sensitivityWithin'],
    group_titles: {const: 'Constituency measures', singleSeat: 'Specifically for\nsingle-seat constituencies',
      sensitivityWithin: 'Seats displaced between lists within parties'},
    show: {const: true, singleSeat: true, sensitivityWithin: true}, footnotes: {},
    side_titles: {const: true, singleSeat: true}, group_options: {singleSeat: 'show_single_seat'},
    headingType: {sensitivityWithin: 'systems'}, group_stats: {sensitivityWithin: ['avg']},
    const: [row('Core row'), row('Additional row', 'show_additional')],
    singleSeat: [row('Single-seat diagnostic')], sensitivityWithin: [row('0.1% coefficient of variation')],
  }
  for (const scaling of ['both', 'party', 'total']) {
    vuedata.group_ids.splice(vuedata.group_ids.indexOf('singleSeat'), 0, scaling)
    vuedata.group_options[scaling] = 'show_scalings'
    vuedata.show[scaling] = true
    vuedata.side_titles[scaling] = true
    vuedata.group_titles[scaling] = scaling
    vuedata[scaling] = [row(`${scaling} deviation`), row(`${scaling} optional`, 'show_additional')]
  }
  const render = () => {
    const app = Vue.createSSRApp(component, {vuedata, ...vuedata})
    app.directive('b-tooltip', {})
    return renderToString(app)
  }
  vuedata.const[0].avg = [{value: 0.022, ci: 0.001, percentage: true}]
  vuedata.const[0].std = [{value: 0.003, ci: null, percentage: true}]
  let html = await render()
  const header = html.split('</thead>')[0]
  assert.equal((header.match(/header-start/g) || []).length, 2)
  assert.match(header, /system-heading data-heading[^\"]*header-start/)
  assert.match(html, /\(2\.2 ± 0\.1\)%/)
  assert.match(html, /0\.3%/)
  assert.match(html, /class="section-title" rowspan="1">Constituency measures/)
  assert.match(html, /Core row/)
  assert.doesNotMatch(html, /Additional row|Single-seat diagnostic/)
  assert.doesNotMatch(html, /both deviation|party deviation|total deviation/)
  settings.show_scalings = true
  html = await render()
  for (const scaling of ['both', 'party', 'total']) {
    assert.ok(html.includes(`${scaling} deviation`))
    assert.ok(!html.includes(`${scaling} optional`))
  }
  settings.show_additional = settings.show_single_seat = true
  html = await render()
  assert.match(html, /class="section-title" rowspan="2">Constituency measures/)
  assert.match(html, /Additional row/)
  assert.match(html, /Single-seat diagnostic/)
  for (const scaling of ['both', 'party', 'total']) {
    assert.ok(html.includes(`${scaling} optional`))
  }
  settings.show_scalings = false
  html = await render()
  assert.doesNotMatch(html, /both deviation|party deviation|total deviation/)
  assert.match(html, /Additional row/)
  const sensitivity = html.match(/<tr[^>]*>(?:(?!<\/tr>)[\s\S])*0\.1% coefficient of variation[\s\S]*?<\/tr>/)[0]
  assert.match(sensitivity, /0\.125 ± 0\.010/)
  assert.doesNotMatch(sensitivity, /0\.050/)

  // Hiding trailing scaling sections must not remove the inter-block gap.
  vuedata.group_ids = ['const', 'both', 'party', 'total', 'parity']
  vuedata.parity = [row('Constituency disparity')]
  vuedata.show.parity = vuedata.side_titles.parity = true
  vuedata.group_titles.parity = 'Geographical balance'
  vuedata.block_headers = {parity: 'Total allocation quality measures'}
  vuedata.block_continues = {const: 'both', both: 'party', party: 'total'}
  for (const showScalings of [false, true, false]) {
    settings.show_scalings = showScalings
    html = await render()
    const beforeTotals = html.split('Total allocation quality measures')[0]
    assert.equal((beforeTotals.match(/class="section-spacer"/g) || []).length, 1)
  }

  // Additional scaling measures require both checkboxes and share one block.
  const additional = ['const', 'both', 'party', 'total'].map(scaling => `additional_${scaling}`)
  vuedata.group_ids = ['const', ...additional, 'both', 'party', 'total', 'parity']
  vuedata.block_headers.additional_const = 'Additional proportionality measures'
  vuedata.block_headers.both = 'Double, party, and national scaling'
  vuedata.block_continues = {additional_const: 'additional_both',
    additional_both: 'additional_party', additional_party: 'additional_total',
    both: 'party', party: 'total'}
  for (const scaling of ['const', 'both', 'party', 'total']) {
    const id = `additional_${scaling}`
    vuedata[id] = [row(`extra ${scaling}`)]
    vuedata.show[id] = vuedata.side_titles[id] = true
    vuedata.group_titles[id] = scaling
    vuedata.group_options[id] = scaling === 'const' ? 'show_additional'
      : ['show_additional', 'show_scalings']
  }
  for (const showAdditional of [false, true]) {
    for (const showScalings of [false, true]) {
      settings.show_additional = showAdditional
      settings.show_scalings = showScalings
      html = await render()
      assert.equal(html.includes('extra const'), showAdditional)
      for (const scaling of ['both', 'party', 'total']) {
        assert.equal(html.includes(`extra ${scaling}`), showAdditional && showScalings)
      }
      if (showAdditional && showScalings) {
        const extraBlock = html.split('Additional proportionality measures')[1]
          .split('Double, party, and national scaling')[0]
        assert.match(extraBlock, /extra both/)
        assert.match(extraBlock, /extra party/)
        assert.match(extraBlock, /extra total/)
      }
    }
  }

  vuedata.group_ids = ['sensitivityWithin', 'sensitivityBetween']
  vuedata.sensitivityBetween = [row('0.1% coefficient of variation')]
  vuedata.show.sensitivityBetween = true
  vuedata.group_stats.sensitivityBetween = ['avg']
  vuedata.side_titles.sensitivityWithin = vuedata.side_titles.sensitivityBetween = true
  vuedata.group_titles.sensitivityWithin = 'list seat displacements'
  vuedata.group_titles.sensitivityBetween = 'party seat displacements'
  vuedata.initial_title = 'List allocation quality measures'
  vuedata.block_headers = {sensitivityWithin: 'Sensitivity'}
  vuedata.block_continues = {sensitivityWithin: 'sensitivityBetween'}
  html = await render()
  const body = html.split('<tbody>')[1]
  assert.equal((body.match(/System A/g) || []).length, 1)
  assert.equal((body.match(/class="section-spacer"/g) || []).length, 1)
  assert.match(html, /class="block-title simulator-title">List allocation quality measures/)
  assert.match(body, /class="block-title simulator-title" colspan="2">Sensitivity/)
  assert.match(body, /system-heading data-heading[^\"]*header-start/)
  assert.match(body, /class="section-title" rowspan="1">list seat displacements/)
  assert.match(body, /class="section-title" rowspan="1">party seat displacements/)

  vuedata.group_messages = {sensitivityBetween: 'Identical totals'}
  html = await render()
  assert.match(html, /class="section-title">party seat displacements/)
  assert.match(html, /class="group-message" colspan="2"/)
  assert.match(html, /Identical totals/)
  assert.equal((html.match(/0\.1% coefficient of variation/g) || []).length, 1)
})
