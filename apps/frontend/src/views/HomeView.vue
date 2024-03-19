<script setup lang="ts">
import Section from '../components/Section.vue';
import ScopeChart from '../components/ScopeChart.vue';
import UserInputVIn from '../components/UserInputVIn.vue';
import UserInputILoad from '../components/UserInputILoad.vue';
import UserInputPWMType from '../components/UserInputPWMType.vue';
import UserInputCapacitor from '../components/UserInputCapacitor.vue';
import UserInputPWM from '../components/UserInputPWM.vue';

import RealPWM from '../components/RealPWM.vue';
import RealILoad from '../components/RealILoad.vue';
import RealVin from '../components/RealVin.vue';
import RealCapacity from '../components/RealCapacity.vue';

import VoutGraph from '../components/VoutGraph.vue';

import router from '../router';
import { useBackendDataStore } from '../stores/back-end-data';
import { ref } from 'vue';

const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const session_id = urlParams.get('session_id');
if (!session_id) {
  console.log('before router push');

  router.push({ path: '/no-session-id-provided' });
  console.log('after router push');
}
const store = useBackendDataStore();
store.setSessionId(session_id!);
store.getIsActive();
store.connectToWebSocket();

const m = ref(0);
</script>

<template>
  <header class="sticky-header">asdasdas</header>
  <div class="background">
    <Section>
      <ScopeChart style="flex: 1"></ScopeChart>
    </Section>
    <Section style="display: flex; height: 35vh; padding: auto">
      <UserInputVIn class="input" />
      <UserInputILoad class="input" />
      <UserInputCapacitor class="input" />
      <UserInputPWM class="input" />
      <UserInputPWMType class="input" />
    </Section>
    <Section style="display: flex; height: 15vh; padding: auto">
      <RealVin class="output" />
      <RealILoad class="output" />
      <RealCapacity class="output" />
      <RealPWM class="output" />
    </Section>
    <Section>
      <VoutGraph />
    </Section>
  </div>
</template>

<style>
.input {
  flex: 1;
  display: flex;
  align-items: center;
}
.output {
  flex: 1;
}
.sticky-header {
  position: sticky;
  top: 0px;
  z-index: 1000;
  height: 6vh;
  background-color: #e3e3e3;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.15), 0 2px 2px rgba(0, 0, 0, 0.15),
    0 4px 4px rgba(0, 0, 0, 0.15), 0 8px 8px rgba(0, 0, 0, 0.15);
}
.background {
  background-color: #eef0f6;
  display: flex;
  flex-direction: column;
}
</style>
