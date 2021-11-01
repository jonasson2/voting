import Vue from "vue"
import Vuex from "vuex"

Vue.use(Vuex)

function setVoteSums(state) {
  console.log("state", state)
  console.log("state.vote_table", state.vote_table)
  console.log("state.vote_sums", state.vote_sums)
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
  waiting_for_data: false,
  server_error: ""
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
    console.log("addSystem, name=", system.name, ", idx=", idx)    
    if (system.name == "System") system.name += "-" + (idx+1).toString();
    state.systems.push(system)
  },
  
  deleteSystem(state, idx) { state.systems.splice(idx, 1); },
  
  deleteAllSystems(state) { state.systems.splice(0, state.systems.length) },
  
  updateSimSettings(state, sim_settings) { state.sim_settings = sim_settings },
  
  updateSysConst(state, sys_consts) { state.sys_constituencies = sys_consts },
  
  addSysConst(state,sys_const) { state.sys_constituencies.push(sys_const) },
  
  deleteResults() { state.results = [] },
  
  notWaiting(state) { state.waiting_for_data = false },
  
  waiting(state) { state.waiting_for_data = true },

  serverError(state, message) {
    console.log("SERVER ERROR: ", message)
    state.server_error = message
  },
  
  clearServerError(state) { state.server_error = '' }
}

const actions = {
  calculate_results(context) {
    console.log("In calculate_results")
    context.commit("waiting")
    Vue.http.post(
      '/api/election/',
      {
        vote_table:     context.state.vote_table,
        rules:          context.state.systems,
        constituencies: context.state.sys_constituencies
      }).then(response => {
        if (response.body.error) {
          context.commit("serverError", response.body.error)
        } else {
          context.state.results = response.body.results
          console.log("store results", context.state.results)
          context.state.sys_constituencies = response.body.constituencies
          // for (var i=0; i<response.body.length; i++){
          //   context.state.systems.splice(i, 1, response.body[i].rules)
          // }
        }
        context.commit("notWaiting")
      })
  },
  recalc_sys_const(context) {
    console.log("In recalc_sys_const")
    context.commit("waiting")
    Vue.http.post(
      '/api/election/',
      {
        vote_table:     context.state.vote_table,
        rules:          context.state.systems,
        constituencies: context.state.sys_constituencies,
        run:            false
      }).then(response => {
        if (response.body.error) {
          context.commit("serverError", response.body.error)
        } else {
          context.state.sys_constituencies = response.body.constituencies
          // for (var i=0; i<response.body.length; i++){
          //   context.state.systems.splice(i, 1, response.body[i].rules)
          // }
        }
        context.commit("notWaiting")
      })
  }
}

export default new Vuex.Store({
  state,
  mutations,
  actions
})
