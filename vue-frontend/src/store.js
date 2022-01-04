import Vue from "vue"
import Vuex from "vuex"

Vue.use(Vuex)

const store = new Vuex.Store({

  state : {
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
      state.vote_table = table
      setVoteSums(state)
    },
    updateVoteSums(state) {
      console.log('updateVoteSums')
      setVoteSums(state)
    },
    addSystem(state, system) {
      let idx = state.systems.length
      if (system.name == "System") system.name += "-" + (idx+1).toString();
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
      console.log("Updating sim_settings, new settings = ", sim_settings)
    },

    setWaitingForData(state) { state.waiting_for_data = true },
    
    clearWaitingForData(state) {
      state.server_error = ''
      Vue.nextTick(()=>{state.waiting_for_data=false})
    },

    setSimulateCreated(state) {state.simulateCreated = true},

    setActiveSystemIndex(state, idx) {
      state.activeSystemIndex = idx
    },

    setSeatSpecOption(state, payload) {
      state.systems[payload.idx].seat_spec_option = payload.opt
    },

    newNumbering(state, idx) {
      findNumbering(state, idx)
      console.log("newNumbering")
    },

    showVoteMatrix(state) {
      state.results = []
      state.show_systems = false
      state.show_simulate = false
    },

    serverError(state, message) {
      console.log("SERVER ERROR: ", message)
      state.server_error = message.split(/\n/g);
      console.log("lengths", message.length, state.server_error.length)
      Vue.nextTick(()=>{state.waiting_for_data=false})
    },
    
    clearServerError(state) { state.server_error = '' },

    initialize(state) {
      console.log("initialize")
      Vue.http.post('/api/capabilities', {}).then(response => {
        if (response.body.error) {
          context.commit("serverError", response.body.error)
        } else {
          state.sim_capabilities = response.body.capabilities;
          state.sim_settings = response.body.sim_settings
          //state.commit("updateSimSettings", response.body.sim_settings)
          //his.$nextTick(()=>this.setSimulateCreated())
          console.log("Created SimulationSettings")
        }
      })
    },

    addBeforeunload(state) {
      if (state.listening) return
      state.listening = true
      console.log("adding event listener")
      window.addEventListener('beforeunload', eventListener)
    },

    removeBeforeunload(state) {
      if (!state.listening) return
      state.listening = false
      console.log("removing event listener")
      window.removeEventListener("beforeunload", eventListener)
    }
  },

  //ACTIONS
  actions : {
    
    showElectoralSystems(context) {
      console.log("showElectoralSystems")
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
      console.log("showSimulate")
    },
    
    uploadElectoralSystems(context, payload) {
      context.commit("setWaitingForData")
      Vue.http.post('/api/settings/upload/', payload.formData).then(
        response => {
          if (response.body.error) {
            context.commit("serverError", response.body.error)
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
            //context.commit("clearWaitingForData")
          }
        })
    },
    uploadAll: function (context, formData) {
      context.commit("setWaitingForData")
      context.commit("deleteAllSystems")
      Vue.http.post("/api/votes/uploadall/", formData).then(
        (response) => {
          if (response.body.error) {
            context.commit("serverError", response.body.error)
          } else {
            console.log("response", response)
            context.commit("updateVoteTable", response.data.vote_table)
            context.commit("updateSystems", response.data.systems)
            context.commit("updateSimSettings", response.data.sim_settings)
            findNumbering(context.state, 0)
            context.commit("clearWaitingForData")
          }
        })
    },
    saveAll(context) {
      let promise;
      promise = axios({
        method: "post",
        url: "/api/votes/saveall",
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
      console.log("In calculate_results")
      Vue.http.post(
        '/api/election/',
        {
          vote_table:     context.state.vote_table,
          systems:        context.state.systems,
        }).then(
          response => {
            if (response.body.error) {
              context.commit("serverError", response.body.error)
            } else {
              context.state.results = response.body.results
              context.state.systems = response.body.systems
            }
            context.commit("clearWaitingForData")
          },
        )
    },
    recalc_sys_const(context) {
      // Refresh the constituencies property of each system according to the value
      // of system.seat_spec_option. If this option is "custom", use values from
      // system.constituencies for constituency names matching the ones of the
      // vote_table, otherwise use use values from vote_table, possibly modified
      // according to the seat_spec_option.
      context.commit("setWaitingForData")
      Vue.http.post(
        '/api/settings/update_constituencies/',
        {
          vote_table:     context.state.vote_table,
          systems:        context.state.systems
        }).then(response => {
          if (response.body.error) {
            context.commit("serverError", response.body.error)
          } else {
            console.log("response.body", response.body)
            response.body.constituencies.forEach(
              (c,i) => context.state.systems[i].constituencies = c
            )
            console.log("sys_const[0]=", context.state.systems[0].constituencies)
          }
          console.log("recalc_sys_const")
          console.log("& sys_const[0]=", context.state.systems[0].constituencies)
          context.commit("clearWaitingForData")
        })
    },
    // Thanks to Pétur Helgi Einarsson for the next two functions
    downloadFile: function (context, promise) {
      console.log("In download file")
      promise.then (
        (response) => {
          const status = response.status;
          if (status != 200) {
            console.log("Server error", response.body.error)
            context.commit("serverError", response.body.error)
          }
          else {
            console.log("Inside status==200")
            console.log("response=", response)
            console.log("headers=", response.headers)
            console.log("content-type", response.headers["content-type"])
            console.log("data", response.data)
            if (response.headers["content-type"] == "application/json") {
              let s,x
              s = String.fromCharCode.apply(null, new Uint8Array(response.data))
              console.log("s=", s)
              eval("x = " + s)
              if ("error" in x) {
                // API returned error instead of actual blob
                context.commit("serverError", x["error"])
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
            let result = link.dispatchEvent(
              new MouseEvent("click", {
                bubbles: true,
                cancelable: true,
                view: window,
              })
            );
            link.remove();
          }
        },
        (response) => {
          console.log("Error:", response);
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
  let vs = state.vote_sums
  let vc = vt.constituencies
  if (vt.parties.length > 0) {
    vs.row = vt.votes.map(y => y.reduce((a, b) => a+b))
    vs.tot = vs.row.reduce((a, b) => a + b, 0)
  }
  else {
    vs.row = 0
    vs.tot = 0
  }
  if (vt.constituencies.length > 0)
    vs.col = vt.votes.reduce((a, b) => a.map((v,i) => v+b[i]))
  else
    vs.col = 0
  vs.cseats = 0
  vs.aseats = 0
  for (var i=0; i<vc.length; i++) {
    vs.cseats += vc[i].num_const_seats
    vs.aseats += vc[i].num_adj_seats
  }
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

function eventListener(e) {
  e.preventDefault()
  e.returnValue = ''
}

export default store
