<script setup lang="ts">
import Section from '../components/Section.vue';
import UserInputVIn from '../components/UserInputVIn.vue';
import UserInputILoad from '../components/UserInputILoad.vue';
import UserInputPWMType from '../components/UserInputPWMType.vue';
import UserInputCapacitor from '../components/UserInputCapacitor.vue';
import UserInputPWM from '../components/UserInputPWM.vue';
import UserInputVLoad from '../components/UserInputVLoad.vue';

import RealPWM from '../components/RealPWM.vue';
import RealILoad from '../components/RealILoad.vue';
import RealVLoad from '../components/RealVLoad.vue';
import RealVin from '../components/RealVin.vue';
import RealCapacity from '../components/RealCapacity.vue';

import ScopeChart from '../components/ScopeChart.vue';
import VoutGraph from '../components/VoutGraph.vue';

import router from '../router';
import { useBackendDataStore } from '../stores/back-end-data';
//import { ref } from 'vue';

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
//const m = ref(0);
</script>

<template>
  <header class="sticky-header">
    <div>Time left: {{ store.timeLeft }}</div>
  </header>

  <div class="background container-fluid">
    <div class="row">
      <!-- 1st component (Schematic Diagram) -->
      <div class="col-lg-6">
        <Section>

          <div v-if="store.typeSchema.type === 'BCK'">
            <h3 class="text-center">DC-DC Buck Converter - Schematic Diagramm</h3>
          </div>
          
          <div v-if="store.typeSchema.type === 'BST'">
            <h3 class="text-center">DC-DC Boost Converter - Schematic Diagramm</h3>
          </div>

          <div class="container-overwritten">

            <div v-if="store.typeSchema.type === 'BCK'">
              <img class="img-fluid" src="../img/buck.svg" />
            </div>
            
            <div v-if="store.typeSchema.type === 'BST'">
              <img class="img-fluid" src="../img/boost.svg" />
            </div>

            <div>
              <RealVin class="real-vin" />
              <RealPWM class="real-pwm" />
              <RealCapacity class="real-capacity" />
              <RealILoad class="real-rload" />

              <RealVLoad class="real-vload" />

              <UserInputVIn class="btn-vin" />
              <div v-if="store.typePWM.type === 'AUT'">
                <UserInputVLoad class="btn-vload" />
              </div>
              <div v-if="store.typePWM.type === 'MAN'">
                <UserInputPWM class="btn-ipwm" />
              </div>
              <UserInputCapacitor class="btn-icap" />
              <UserInputILoad class="btn-rload" />
              <UserInputPWMType class="btn-ipwm-type" />
            </div>
          </div>
        </Section>
      </div>

      <div class="col-lg-6">
        <Section>
          <h3 class="text-center">Experiment recommendations</h3>
          <div>
            <p class="lead numbered-paragraph">1. Set Manual PWM mode.</p>
            <p class="lead numbered-paragraph">
              2. Set desired C<sub>F</sub> and R<sub>Load</sub> values.
            </p>
            <p class="lead numbered-paragraph">3. Set initial value of PWM duty cycle.</p>
            <p class="lead numbered-paragraph">4. Add point to "Output voltage vs PWM" chart.</p>
            <p class="lead numbered-paragraph">5. Increase the level of PWM duty cycle.</p>
            <p class="lead numbered-paragraph">6. Repeat 4 and 5 until PWM duty cycle is 100%.</p>
            <p class="lead numbered-paragraph">7. Save "Output voltage vs PWM" chart.</p>
          </div>
        </Section>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-6">
        <Section>
          <h3 class="text-center">Oscilloscope</h3>
          <ScopeChart />
        </Section>
      </div>

      <div class="col-lg-6">
        <Section>
          <h3 class="text-center">Output Voltage vs PWM</h3>
          <VoutGraph />
        </Section>
      </div>
    </div>
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
