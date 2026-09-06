import Vue from "vue"
import Vuex from "vuex"
import { calculateVoteSums, normalizeVoteTable } from "./voteTable.js"

const store = new Vuex.Store({

  state : {
    vote_table: {
      name: "Default Example",
      parties: ["A", "B"],
      votes: [
        [1500, 2000],
        [2500, 1700],
      ],
      pruned: [0, 0],
      constituencies: [
        { name: "I", num_fixed_seats: 10, num_adj_seats: 2 },
        { name: "II", num_fixed_seats: 10, num_adj_seats: 3 },
      ],
      party_vote_info: {
        name: "–",
        num_fixed_seats: 0,
        num_adj_seats: 0,
        votes: [],
        specified: false,
        total: 0,
        pruned: 0,
      },
      party_vote_basis: "totals",
    },
    vote_sums: {
      cseats: 0,
      aseats: 0,
      row: {},
      col: [],
      tot: 0,
      pruned: 0,
    },
    systems: [],
    system_numbering: [],
    activeSystemIndex: -1,   // Includes the <-- and --> tabs
    sim_settings: {},
    sim_capabilities: {},
    results: [],
    server_error: "",
    show_simulate: false,
    show_systems: false,
    waiting_for_data: true,
    listening: false,
    simulateCreated: false
  },

  // MUTATIONS
  mutations : {
    updateVoteTable(state, table) {
      normalizeVoteTable(table)
      state.vote_table = table
      setVoteSums(state)
      state.vote_table.name = table.name
    },
    updateVoteSums(state) {
      setVoteSums(state)
    },
    threshold_method(state, systemidx) {
      let method = state.systems[systemidx].adjustment_method
      if (method == 'icelandic-law' || method == 'ice-shares'){
        state.systems[systemidx].adjustment_threshold = 5
      }
      else if (method == 'norwegian-law') {
        state.systems[systemidx].adjustment_threshold = 4
      }
      else{
        state.systems[systemidx].adjustment_threshold = 0
      }
    },
    addSystem(state, system) {
      let idx = state.systems.length
      if (system.name == "System") system.name += "-" + (idx+1).toString();
      if (idx > 0) {
        system.primary_divider = state.systems[idx-1].primary_divider
        system.adj_determine_divider = state.systems[idx-1].adj_determine_divider
        system.adj_alloc_divider = state.systems[idx-1].adj_alloc_divider
        system.adjustment_threshold = state.systems[idx-1].adjustment_threshold
        system.adjustment_threshold_seats = state.systems[idx-1].adjustment_threshold_seats
        system.adj_threshold_choice = state.systems[idx-1].adj_threshold_choice
        system.constituency_threshold = state.systems[idx-1].constituency_threshold
        system.adjustment_method = state.systems[idx-1].adjustment_method
        system.seat_spec_options.const = state.systems[idx-1].seat_spec_options.const
        system.seat_spec_options.party = state.systems[idx-1].seat_spec_options.party
        system.compare_with = state.systems[idx-1].compare_with
        system.parties = state.systems[idx-1].parties
      }
      state.systems.push(system)
      findNumbering(state, idx)
    },
    updateComparisonSystems(state, list) {
      for (var sys of state.systems) {
        sys.compare_with = list.includes(sys.name) ? true : false
      }
    },
    
    deleteSystem(state, idx) {
      state.systems.splice(idx, 1);
      findNumbering(state, idx)
    },
    
    deleteAllSystems(state) {
      state.systems.splice(0, state.systems.length)
      state.numbering = []
      state.activeSystemIndex = -1
    },
    
    updateSystems(state, systems) {state.systems = systems},

    updateSimSettings(state, sim_settings) {
      state.sim_settings = sim_settings
    },

    setWaitingForData(state) { state.waiting_for_data = true },
    
    clearWaitingForData(state) {
      Vue.nextTick(()=>{state.waiting_for_data=false})
    },

    setSimulateCreated(state) {state.simulateCreated = true},

    setActiveSystemIndex(state, idx) {
      state.activeSystemIndex = idx
    },

    setConstSpecOption(state, payload) {
      state.systems[payload.idx].seat_spec_options.const = payload.opt
    },

    newNumbering(state, idx) {
      findNumbering(state, idx)
    },

    showVoteMatrix(state) {
      state.results = []
      state.show_systems = false
      state.show_simulate = false
    },

    serverError(state, message) {
      state.waiting_for_data = false
      if (!message)
        message = "Error: Unknown error with null message (perhaps jasonify with illegal"
         + " arguments such as numpy data)"
      else if (Number.isInteger(message)) {
        if (message == 500)
          message = "Error: Uncaught exception in backend (possibly logged to console)"
        else if (message == 0)
          message = "Error: Server not responding"
        else
          message = "Unknown error"
      }
      else if (typeof message !== "string") {
        if ('error' in message)
          message = message.error
        else
          message = "Error: Unknown error with non-string message"
      }
      state.server_error = message.split(/\n/g);
    },
    
    clearServerError(state) { state.server_error = '' },

    addBeforeunload(state) {
      if (state.listening) return
      state.listening = true
      window.addEventListener('beforeunload', eventListener)
    },

    removeBeforeunload(state) {
      if (!state.listening) return
      state.listening = false
      window.removeEventListener("beforeunload", eventListener)
    }
  },

  //ACTIONS
  actions : {
    
    initialize(context) {
      Vue.http.post('api/capabilities/', {}).then(
        response => {
          if (error(response)) {
            context.commit("serverError", response.body)
          } else {
            context.state.sim_capabilities = response.body.capabilities;
            context.state.sim_settings = response.body.sim_settings
          }
        },
        response => context.commit("serverError", response.status)
      )
    },

    showElectoralSystems(context) {
      context.state.results = []
      context.state.show_systems = true
      context.state.show_simulate = false
      context.dispatch("recalc_sys_const")
    },

    showElection(context) {
      context.state.show_systems = false
      context.state.show_simulate = false
      context.dispatch("calculate_results")
    },
    
    showSimulate(context) {
      context.state.results = []
      context.state.show_systems = false
      context.state.show_simulate = true
      context.dispatch("recalc_sys_const")
    },
    
    uploadElectoralSystems(context, payload) {
      context.commit("setWaitingForData")
      Vue.http.post('api/settings/upload/', payload.formData).then(
        response => {
          if (error(response)) {
            context.commit("serverError", response.body)
          } else {
            if (payload.replace){
              context.commit("deleteAllSystems")
            }
            let systems = response.data.systems
            for (var i=0; i < systems.length; i++) {
              if (!("compare_with" in systems[i])) systems[i].compare_with = false
              context.commit("addSystem", systems[i])
            }
            findNumbering(context.state, 0)
            context.commit("updateSimSettings", response.data.sim_settings);
            context.dispatch("recalc_sys_const")
            context.commit("clearWaitingForData")
          }
        },
        response => {
          context.commit('serverError', response.status)
        }
      )
    },
    uploadAll: function (context, formData) {
      context.commit("setWaitingForData")
      Vue.http.post("api/uploadall/", formData).then(
        (response) => {
          if (error(response)) {
            context.commit("serverError", response.body)
          } else {
            context.commit("deleteAllSystems")
            context.commit("updateVoteTable", response.data.vote_table)
            context.commit("updateSystems", response.data.systems)
            context.commit("updateSimSettings", response.data.sim_settings)
            findNumbering(context.state, 0)
            context.commit("clearWaitingForData")
          }
        },
        response => context.commit("serverError", response.status)
      )
    },
    saveAll(context) {
      let promise;
      promise = axios({
        method: "post",
        url: "api/saveall/",
        data: {
          vote_table: context.state.vote_table,
          systems: context.state.systems,
          sim_settings: context.state.sim_settings
        },
        responseType: "arraybuffer",
      });
      context.dispatch("downloadFile", promise)
      context.commit("removeBeforeunload")
    },
    
    calculate_results(context) {
      context.commit("setWaitingForData")
      Vue.http.post(
        'api/election/',
        {
          vote_table:     context.state.vote_table,
          systems:        context.state.systems,
        }).then(
          response => {
            if (error(response)) {
              context.commit("serverError", response.body)
            } else {
              context.state.results = response.body.results
              context.state.systems = response.body.systems
            }
            context.commit("clearWaitingForData")
          },
          response => context.commit("serverError", response.status)
        )
    },
    recalc_sys_const(context) {
      // Refresh the constituencies property of each system according to the value
      // of system.seat_spec_options.const. If this option is "custom", use values from
      // system.constituencies for constituency names matching the ones of the
      // vote_table, otherwise use use values from vote_table, possibly modified
      // according to the seat_spec_options.const.
      context.commit("setWaitingForData")
      Vue.http.post(
        'api/settings/update_constituencies/',
        {
          vote_table:     context.state.vote_table,
          systems:        context.state.systems
        }).then(response => {
          if (error(response)) {
            context.commit("serverError", response.body)
          } else {
            response.body.constituencies.forEach(
              (c,i) => context.state.systems[i].constituencies = c
            )
            response.body.nat_seats.forEach(
              (n,i) => context.state.systems[i].nat_seats = n
            )
          }
          context.commit("clearWaitingForData")
        }, response => context.commit("serverError", response.status))
    },
    // Thanks to Pétur Helgi Einarsson for the next two functions
    downloadFile: function (context, promise) {
      promise.then (
        (response) => {
          const status = response.status;
          if (status != 200) {
            context.commit("serverError", response.body)
          }
          else {
            if (response.headers["content-type"].startsWith("application/json")) {
              let payload
              try {
                payload = JSON.parse(new TextDecoder().decode(response.data))
              } catch (error) {
                context.commit("serverError", "The server returned invalid JSON")
                return
              }
              if ("error" in payload) {
                // API returned error instead of actual blob
                context.commit("serverError", payload["error"])
                return
              }
            }
            let link = document.createElement("a");
            const [type, downloadname] = parse_headers(response.headers);
            const blob = new Blob([response.data], {type: type});
            const blobUrl = URL.createObjectURL(blob);
            link.href = blobUrl;
            link.download = downloadname;
            document.body.appendChild(link);
            // Dispatch click event on the link (this is necessary
            // as link.click() does not work in the latest Firefox
            link.dispatchEvent(
              new MouseEvent("click", {
                bubbles: true,
                cancelable: true,
                view: window,
              })
            );
            link.remove();
            URL.revokeObjectURL(blobUrl);
          }
        },
        (response) => {
          context.commit("serverError", response.status || response.message)
        }
      )
    }
  }
})

function parse_headers(headers) {
  // Return type and name for download file
  var content_type = headers["content-type"];
  var content_disposition = headers["content-disposition"];
  let parts = content_disposition.split(";");
  let download_name = "Example.xlsx"
  for (var i_part in parts) {
    let part = parts[i_part];
    let filename_pos = part.indexOf("filename=");
    if (filename_pos != -1) {
      filename_pos += "filename=".length;
      download_name = part.substring(filename_pos);
    }
  }
  return [content_type, download_name]
}

function setVoteSums(state) {
  let vt = state.vote_table
  normalizeVoteTable(vt)
  const sums = calculateVoteSums(vt)
  vt.party_vote_info.total = sums.partyVoteTotal
  delete sums.partyVoteTotal
  Object.assign(state.vote_sums, sums)
}

function findNumbering(state, asi) {
  let n = state.systems.length
  if (asi > n-1) asi = n-1
  let num = []
  for (var i=0; i < n; i++) {
    if (n > 1 && i > 0 && i == asi) num.push(-2)
    num.push(i)
    if (n > 1 && i < n-1 && i == asi) num.push(-1)
  }
  state.system_numbering = num
  state.activeSystemIndex = asi
}

function error(response) {
  return !response.body || response.body.error
}

function eventListener(e) {
  e.preventDefault()
  e.returnValue = ''
}

export default store
