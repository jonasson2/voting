import Vue from 'vue'
import VueResource from 'vue-resource';
import BootstrapVue from 'bootstrap-vue'
Vue.use(VueResource);
Vue.use(BootstrapVue);
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

import Main from './Main.vue'
import store from './store.js'

new Vue({
  el: "#app",
  store,
  components: {Main},
  render: h => h(Main),
})
