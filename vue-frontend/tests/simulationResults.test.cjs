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
  const settings = {show_additional: false, show_single_seat: false}
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
    group_titles: {const: 'Local measures', singleSeat: 'Specifically for\nsingle-seat constituencies',
      sensitivityWithin: 'Seats displaced between lists within parties'},
    show: {const: true, singleSeat: true, sensitivityWithin: true}, footnotes: {},
    side_titles: {const: true, singleSeat: true}, group_options: {singleSeat: 'show_single_seat'},
    headingType: {sensitivityWithin: 'systems'}, group_stats: {sensitivityWithin: ['avg']},
    const: [row('Core row'), row('Additional row', 'show_additional')],
    singleSeat: [row('Single-seat diagnostic')], sensitivityWithin: [row('0.1% CoV')],
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
  assert.match(html, /class="section-title" rowspan="1">Local measures/)
  assert.match(html, /Core row/)
  assert.doesNotMatch(html, /Additional row|Single-seat diagnostic/)
  settings.show_additional = settings.show_single_seat = true
  html = await render()
  assert.match(html, /class="section-title" rowspan="2">Local measures/)
  assert.match(html, /Additional row/)
  assert.match(html, /Single-seat diagnostic/)
  const sensitivity = html.match(/<tr[^>]*>(?:(?!<\/tr>)[\s\S])*0\.1% CoV[\s\S]*?<\/tr>/)[0]
  assert.match(sensitivity, /0\.125 ± 0\.010/)
  assert.doesNotMatch(sensitivity, /0\.050/)

  vuedata.group_ids = ['sensitivityWithin', 'sensitivityBetween']
  vuedata.sensitivityBetween = [row('0.1% CoV')]
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
  assert.equal((html.match(/0\.1% CoV/g) || []).length, 1)
})
