const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const {resolve} = require('node:path')
const {test} = require('node:test')
const Vue = require('vue')
const {renderToString} = require('@vue/server-renderer')
const {parse, compileTemplate} = require('@vue/compiler-sfc')

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
      results: [[[5, 7], [8, 5]], [[6, 6], [7, 6]]].map(values => ({
        display_results: values, demo_tables: [{}], ties: [],
      })),
      vote_table: {parties: ['A', 'B'], party_vote_info: {specified: false}},
      resultIndex: 0,
    }),
    methods: {
      openDownload() {},
      saveResults() {},
      resultTabKey(system) { return system.name },
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
  assert.match(panels[1], /<pre[^>]*>\[\[6,6\],\[7,6\]\]<\/pre>/)
  assert.doesNotMatch(html, /There are no electoral systems specified/)
})
