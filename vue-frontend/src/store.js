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
    activeTabIndex: -1,   // Includes the <-- and --> tabs
    sim_settings: {},
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
      state.activeTabIndex = -1
    },
    
    updateSystems(state, systems) {state.systems = systems},

    updateSimSettings(state, sim_settings) { state.sim_settings = sim_settings },

    setWaitingForData(state) { state.waiting_for_data = true },
    
    clearWaitingForData(state) {Vue.nextTick(()=>{state.waiting_for_data=false})},

    setSimulateCreated(state) {state.simulateCreated = true},

    setActiveTabIndex(state, idx) {state.activeTabIndex = idx},

    setSeatSpecOption(state, payload) {
      console.log("sssi", state.systems[0].seat_spec_option)
      state.systems[payload.idx].seat_spec_option = payload.opt
      console.log("ssso", state.systems[0].seat_spec_option)
    },

    newNumbering(state, idx) {findNumbering(state, idx)},

    showSimulate(state) {
      state.results = []
      state.show_systems = false
      state.show_simulate = true
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
    },
    
    clearServerError(state) { state.server_error = '' },

    initialize(state) {
      console.log("initialize")
    },

    addBeforeunload(state) {
      if (state.listening) return
      state.listening = true
      console.log("adding event listener")
      window.addEventListener('beforeunload', function (e) {
        e.preventDefault()
        e.returnValue = ''
      })
    },
  },

  //ACTIONS
  actions : {
    
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
    
    uploadElectoralSystems(context, payload) {
      context.commit("setWaitingForData")
      if (payload.replace){
        context.commit("deleteAllSystems")
      }
      Vue.http.post('/api/settings/upload/', payload.formData).then(response => {
        let systems = response.data.systems
        for (var i=0; i < systems.length; i++) {
          if (!("compare_with" in systems[i])) systems[i].compare_with = false
          context.commit("addSystem", systems[i])
        }
        findNumbering(context.state, 0)
        context.commit("updateSimSettings", response.data.sim_settings);
        context.commit("clearWaitingForData")
      });
    },
    uploadAll: function (context, formData) {
      context.commit("setWaitingForData")
      context.commit("deleteAllSystems")
      Vue.http.post("/api/votes/uploadall/", formData).then(
        (response) => {
          console.log("response", response)
          context.commit("updateVoteTable", response.data.vote_table)
          context.commit("updateSystems", response.data.systems)
          context.commit("updateSimSettings", response.data.sim_settings)
          findNumbering(context.state, 0)
          context.commit("clearWaitingForData")
        },
        (response) => {
          context.commit("serverError", "Cannot upload votes from this file")
          context.commit("clearWaitingForData")
        },
      )
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
      //this.$emit("download-file", promise);
      context.dispatch("downloadFile", promise)
    },
    calculate_results(context) {
      context.commit("setWaitingForData")
      console.log("In calculate_results")
      Vue.http.post(
        '/api/election/',
        {
          vote_table:     context.state.vote_table,
          systems:        context.state.systems,
        }).then(response => {
          if (response.body.error) {
            context.commit("serverError", response.body.error)
          } else {
            context.state.results = response.body.results
          }
          context.commit("clearWaitingForData")
        })
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
          systems:        context.state.systems,
          run:            false,
        }).then(response => {
          if (response.body.error) {
            context.commit("serverError", response.body.error)
          } else {
            response.body.constituencies.forEach(
              (c,i) => context.state.systems[i].constituencies = c
            )
          }
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
            if (response.headers["content-type"] == "application/json") {
              let s,x
              s = String.fromCharCode.apply(null, new Uint8Array(response.data))
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
            link.dispatchEvent(
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

function findNumbering(state, asi) {
  let n = state.systems.length
  if (asi > n-1) asi = n-1
  let num = []
  for (var i=0; i < n; i++) {
    if (n > 1 && i > 0 && i == asi) num.push(-2)
    num.push(i)
    if (n > 1 && i < n-1 && i == asi) num.push(-1)
  }
  console.log("numbering=", num)
  state.system_numbering = num
  if (asi==0) state.activeTabIndex = 0;
}

export default store
