<!-- https://stackoverflow.com/questions/61497825/bootstrap-vue-custom-border-column-style-and-custom-border-row-style-on-b-table -->

<template>
  <div>
  <b-navbar toggleable="md" type="dark" variant="info">
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="#/">Election simulator</b-navbar-brand>
  </b-navbar>
  <b-alert
    :show="server_error != ''"
    dismissible
    @dismissed="clearServerError()"
    variant="danger"
    >
    <template v-for="(line, idx) in server_error">
      <br v-if="idx>0">
      {{line}}
    </template>
  </b-alert>
  <b-tabs
    active-nav-item-class="font-weight-bold"
    no-key-nav card
    >
    <b-tab title="Source votes and seats" active @click="showVoteMatrix">
      <!-- <p>Specify reference votes and seat numbers</p> -->
      <VoteMatrix
        >
      </VoteMatrix>
    </b-tab>
    <b-tab title="Electoral systems" @click="showElectoralSystems">
      <!-- <p>Define one or several electoral systems by specifying apportionment -->
        <!--   rules and modifying seat numbers</p> -->
      <ElectoralSystems>
      </ElectoralSystems>
    </b-tab>
    <b-tab title="Single election" @click="showElection">
      <!-- <p>Calculate results for the reference votes and a selected electoral system</p> -->      
      <Election>
      </Election>
    </b-tab>
    <b-tab title="Simulated elections" @click="showSimulate()">
      <!-- <P>Simulate several elections and compute results for each specified electoral system</p> -->
      <Simulate>
      </Simulate>
    </b-tab>
    <b-tab title="Help">
      <Intro>
      </Intro>
    </b-tab>
  </b-tabs>
</b-card>
</div>
</template>

<script>
import Election from './Election.vue'
import ElectoralSystems from './ElectoralSystems.vue'
import Simulate from './Simulate.vue'
import VoteMatrix from './VoteMatrix.vue'
import Intro from './Intro.vue'
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
  components: {
    VoteMatrix,
    Election,
    Simulate,
    ElectoralSystems,
    Intro,
  },
  
  computed: {
    ...mapState([
      'server_error'
    ]),
  },
  //computed: mapState(['server_error']),
  
  data: function() {
    return {
      fields: [{ key: 'first_name', label: 'First' },'last_name', 'age'],
      items: [
        { isActive: true, age: 40, first_name: 'Dickerson', last_name: 'Macdonald' },
        { isActive: false, age: 21, first_name: 'Larsen', last_name: 'Shaw' },
        { isActive: false, age: 89, first_name: 'Geneva', last_name: 'Wilson' },
        { isActive: true, age: 38, first_name: 'Jami', last_name: 'Carney' }
      ]
    }
  },

  methods: {
    ...mapMutations([
      "clearServerError",
      "showVoteMatrix",
      "initialize"
    ]),
    ...mapActions([
      "showElection",
      "showElectoralSystems",
      "showSimulate",
    ]),
  },
  mounted: function() {
    console.log("Main created")
    this.initialize()
  },
}
</script>
