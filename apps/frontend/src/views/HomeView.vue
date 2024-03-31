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
  <header class="sticky-header">
    <div> Time left: {{ store.timeLeft }}</div>
  </header>
  
  <div class="background container-fluid">

    <div class="row">

      <!-- 1st component (Schematic Diagram) -->
      <div class="col-lg-6 border border-dark" style="background-color:lavender;">

        <Section>
          <h3 class="font-weight-bold text-center">DC-DC Buck Converter - Schematic Diagramm</h3>
          <div class="container-overwritten">
        
            <img class="img-fluid" src="../img/buck.svg"/>
            
              <RealVin class="real-vin"/>
              <RealPWM class="real-pwm"/>
              <RealCapacity class="real-capacity"/>
              <RealILoad class="real-rload"/>
              <UserInputVIn class="btn-vin" />
              <UserInputPWM class="btn-ipwm" />
              <UserInputCapacitor class="btn-icap" />
              <UserInputILoad class="btn-rload" />
              <UserInputPWMType class="btn-ipwm-type" />
          </div>
        </Section>   
      
      </div>
    
      <div class="col-lg-6 border border-dark" style="background-color:lavender;">
    
        <Section>
          <h3 class="font-weight-bold text-center">Experiment recommendations</h3>
          <div>
            <p class="lead numbered-paragraph">1. Set Manual PWM mode.</p>
            <p class="lead numbered-paragraph">2. Set desired C<sub>F</sub> and R<sub>Load</sub> values.</p>
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
      <div class="col-lg-6 border border-dark" style="background-color:lavender;">
        <Section>
          <h3 class="font-weight-bold text-center">Oscilloscope</h3>
          <ScopeChart style="flex: 1"></ScopeChart>
        </Section>
      </div>

      <div class="col-lg-6 border border-dark" style="background-color:lavender;">

        <Section>
          <h3 class="font-weight-bold text-center">Output Voltage vs PWM</h3>
          <VoutGraph />
            
        </Section>
      </div>
    </div>
  </div>
</template>

<style>

.sticky-header {
  position: sticky;
  top: 0px;
  z-index: 1000;
  height: 6vh;
  background-color: #e3e3e3;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.15), 0 2px 2px rgba(0, 0, 0, 0.15),
    0 4px 4px rgba(0, 0, 0, 0.15), 0 8px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  justify-content: center;
  align-items: center;
}

.numbered-paragraph {
  margin: 0px; 
  margin-left: 30px;
}

.container-overwritten {
  position: relative;
  display: inline-block;
}

.container-overwritten .btn-vin {
  position: absolute;
  top: 58%;
  left: 15%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-ipwm {
  position: absolute;
  top: 58%;
  left: 36%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-icap {
  position: absolute;
  top: 58%;
  left: 69%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 1px;
}

.btn-ipwm-type {
  position: absolute;
  top: 90%;
  left: 48%;
  transform: translate(-50%, -50%);
  padding: 1px 1px;
  border-radius: 5px;
}

.container-overwritten .btn-rload {
  position: absolute;
  top: 58%;
  left: 96%;
  font-size: 16px;
  transform: translate(-50%, -50%);
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .real-vin {
  position: absolute;
  top: 27%;
  left: 15%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  padding: 1px;
  border: 1px solid black;
  background-color: white;
}

.container-overwritten .real-pwm {
  position: absolute;
  top: 27%;
  left: 36%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  padding: 1px;
  border: 1px solid black;
  background-color: white;
}

.container-overwritten .real-capacity {
  position: absolute;
  top: 27%;
  left: 69%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  padding: 1px;
  border: 1px solid black;
  background-color: white;  
}

.container-overwritten .real-rload {
  position: absolute;
  top: 27%;
  left: 96%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  padding: 1px;
  border: 1px solid black;
  background-color: white;
}



</style>
