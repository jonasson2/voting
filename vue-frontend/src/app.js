import Vue, { createApp } from 'vue'
import VueResource from 'vue-resource';
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

import Main from './Main.vue'
import store from './store.js'
import autowidth from './autowidth.js'

const app = createApp(Main)
app.config.compatConfig = { MODE: 2 }
app.use(store)
app.use(VueResource)
// vue-resource is a Vue 2 plugin. Its HTTP client is installed on the Vue 3
// compatibility app, while legacy store code accesses it through Vue.http.
Vue.http = app.http
app.use(BootstrapVue)
app.directive('autowidth', autowidth)
app.mount('#app')
