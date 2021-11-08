import Vue from "vue"
import Vuex from "vuex"

Vue.use(Vuex)

function setVoteSums(state) {
  let vt = state.vote_table
  let vs = state.vote_sums
  let vc = vt.constituencies
  vs.row = vt.votes.map(y => y.reduce((a, b) => a+b))
  vs.col = vt.votes.reduce((a, b) => a.map((v,i) => v+b[i]))
  vs.tot = vs.row.reduce((a, b) => a + b, 0)
  vs.cseats = 0
  vs.aseats = 0
  for (var i=0; i<vc.length; i++) {
    vs.cseats += vc[i].num_const_seats
    vs.aseats += vc[i].num_adj_seats
  }
}

const state = {
  vote_table: {
    name: "Example values",
    parties: ["A", "B"],
    votes: [
      [1500, 2000],
      [2500, 1700],
    ],
    constituencies: [
      { name: "I", num_const_seats: 10, num_adj_seats: 2 },
      { name: "II", num_const_seats: 10, num_adj_seats: 3 },
    ],
  },
  vote_sums: {
    cseats: 0,
    aseats: 0,
    row: {},
    col: [],
    tot: 0,
  },
  systems: [],
  sys_constituencies: [],
  sim_settings: {},
  results: [],
  server_error: "",
  show_simulate: false,
}

const mutations = {
  updateVoteTable(state, table) {
    state.vote_table = table
    setVoteSums(state)
  },
  updateVoteSums(state) {
    setVoteSums(state)
  },
  addSystem(state, system) {
    let idx = state.systems.length
    if (system.name == "System") system.name += "-" + (idx+1).toString();
    state.systems.push(system)
  },
  updateComparisonSystems(state, list) {
    for (var sys of state.systems) {
      sys.compare_with = list.includes(sys.name) ? true : false
    }
  },
  
  deleteSystem(state, idx) { state.systems.splice(idx, 1); },
  
  deleteAllSystems(state) { state.systems.splice(0, state.systems.length) },
  
  updateSimSettings(state, sim_settings) { state.sim_settings = sim_settings },
  
  updateSysConst(state, sys_consts) { state.sys_constituencies = sys_consts },
  
  addSysConst(state,sys_const) { state.sys_constituencies.push(sys_const) },
  
  showDataTabs(state) { state.results = []; state.show_simulate = false },

  showSimulate(state) {state.show_simulate = true},
  
  serverError(state, message) {
    console.log("SERVER ERROR: ", message)
    state.server_error = message
  },
  
  clearServerError(state) { state.server_error = '' }
}

const actions = {
  calculate_results(context) {
    console.log("In calculate_results")
    Vue.http.post(
      '/api/election/',
      {
        vote_table:     context.state.vote_table,
        systems:        context.state.systems,
        constituencies: context.state.sys_constituencies,
        run:            true,
      }).then(response => {
        if (response.body.error) {
          context.commit("serverError", response.body.error)
        } else {
          context.state.sys_constituencies = response.body.constituencies
          context.state.results = response.body.results
        }
      })
  },
  recalc_sys_const(context) {
    // Refresh the constituencies property of each system according to the value
    // of system.seat_spec_option. If this option is "custom", use values from
    // system.constituencies for constituency names matching the ones of the
    // vote_table, otherwise use use values from vote_table, possibly modified
    // according to the seat_spec_option.
    console.log("In recalc_sys_const")
    Vue.http.post(
      '/api/election/',
      {
        vote_table:     context.state.vote_table,
        systems:          context.state.systems,
        constituencies: context.state.sys_constituencies,
        run:            false,
      }).then(response => {
        if (response.body.error) {
          context.commit("serverError", response.body.error)
        } else {
          context.state.sys_constituencies = response.body.constituencies
        }
      })
  }
}

export default new Vuex.Store({
  state,
  mutations,
  actions
})
