const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const Vue = require('vue')
const {renderToString} = require('@vue/server-renderer')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

test('all step-by-step demonstration tables are rendered', () => {
  const filename = resolve(__dirname, '../src/Election.vue')
  const {descriptor} = parse(readFileSync(filename, 'utf8'))
  assert.match(
    descriptor.template.content,
    /v-for="\(table, demoIndex\) in results\[activeTabIndex\]\.demo_tables"/,
  )
  assert.match(descriptor.template.content, /:table="table"/)
})

test('each election result appears under its own named tab', async () => {
  const filename = resolve(__dirname, '../src/Election.vue')
  const {descriptor} = parse(readFileSync(filename, 'utf8'))
  const {code, errors} = compileTemplate({
    source: descriptor.template.content,
    filename,
    id: 'election-results-test',
    compilerOptions: {mode: 'function'},
  })
  assert.deepEqual(errors, [])
  assert.match(descriptor.template.content,
    /:key="resultTabKey\(system\)"/)
  const app = Vue.createSSRApp({
    render: new Function('Vue', code)(Vue),
    data: () => ({
      systems: [{name: "D'Hondt"}, {name: 'Sainte-Laguë'}],
      results: [
        {display_results: [[5, 7], [8, 5]], demo_tables: [{}], ties: [{
          stage: 'Party totals', candidates: ['A', 'B'], selected: 'A',
          scores: [400, 200],
        }]},
        {display_results: [[6, 6], [7, 6]], demo_tables: [{}], ties: []},
      ],
      vote_table: {parties: ['A', 'B'], party_vote_info: {specified: false}},
      resultIndex: 0,
    }),
    methods: {
      openDownload() {},
      saveResults() {},
      resultTabKey(system) { return system.name },
      formatTieScore(score) { return String(score) },
    },
  })
  // Shallow rendering checks the real template's tab titles and slot wiring.
  for (const name of ['b-tabs', 'b-container', 'b-button', 'b-alert', 'b-row',
    'b-col', 'DownloadNameDialog', 'ResultDemonstration']) {
    app.component(name, {
      render() { return Vue.h('div', this.$slots.default?.()) },
    })
  }
  app.component('b-tab', {
    props: ['title'],
    render() {
      return Vue.h('section', [
        Vue.h('button', this.title ?? this.$slots.title?.()),
        this.$slots.default?.(),
      ])
    },
  })
  app.component('ResultMatrix', {
    props: ['values'],
    render() { return Vue.h('pre', JSON.stringify(this.values)) },
  })
  app.directive('b-tooltip', {})

  const html = await renderToString(app)
  assert.match(html, /<button>D&#39;Hondt<\/button>/)
  assert.match(html, /<button>Sainte-Laguë<\/button>/)
  const panels = html.split('<section>').slice(1).map(part => part.split('</section>')[0])
  assert.equal(panels.length, 2)
  assert.match(panels[0], /<pre[^>]*>\[\[5,7\],\[8,5\]\]<\/pre>/)
  assert.match(panels[0], /Tied scores:\s*400; 200\./)
  assert.match(panels[1], /<pre[^>]*>\[\[6,6\],\[7,6\]\]<\/pre>/)
  assert.doesNotMatch(html, /There are no electoral systems specified/)
})

test('seat table renders votes per seat, including total and national rows', async () => {
  const filename = resolve(__dirname, '../src/components/ResultMatrix.vue')
  const {descriptor} = parse(readFileSync(filename, 'utf8'))
  const {code, errors} = compileTemplate({
    source: descriptor.template.content, filename, id: 'votes-per-seat-test',
    compilerOptions: {mode: 'function'},
  })
  assert.deepEqual(errors, [])
  const {formatNumber} = await import('../src/numberFormat.js')
  const script = descriptor.script.content
    .replace(/^import .*$/gm, '')
    .replace('export default', 'return')
  const component = new Function('mapState', 'formatNumber', script)(
    () => ({display_settings: () => ({fractional_digits: 2})}), formatNumber)
  component.render = new Function('Vue', code)(Vue)
  const app = Vue.createSSRApp(component, {
    constituencies: [{name: 'A'}, {name: 'B'}], parties: ['P'],
    values: [[3, 3], [0, 0], [3, 3], [2, 2], [5, 5]],
    votes_per_seat: [1234.5, null, 1234.5],
    party_votes_specified: true, party_votes_name: 'National',
  })
  app.component('b-container', {render() { return Vue.h('div', this.$slots.default?.()) }})
  app.directive('b-tooltip', {})
  const html = await renderToString(app)
  assert.match(html, /Votes per seat/)
  const rows = html.match(/<tr[\s\S]*?<\/tr>/g)
  assert.match(rows[1], /1,234\.50/)
  assert.match(rows[2], /<td class="displayright">–<\/td>/)
  assert.match(rows[3], /1,234\.50/)
  assert.match(rows[4], /<td class="displayright">–<\/td>/)
  assert.match(rows[5], /<td class="displayright">–<\/td>/)
})
