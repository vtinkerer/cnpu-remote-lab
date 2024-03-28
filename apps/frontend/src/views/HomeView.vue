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
      <div class="col-md-6 border border-dark" style="background-color:lavender;">

        <Section>
          <h2 class="font-weight-bold text-center">DC-DC Buck Converter - Schematic Diagramm</h2>
          <div class="container-overwritten">
            
        
            <img class="img-fluid" src="../img/buck.svg"/>
         
            
              <UserInputVIn class="btn-vin" />
              <UserInputILoad class="btn-iload" />
              <UserInputCapacitor class="btn-icap" />
              <UserInputPWM class="btn-ipwm" />
              <UserInputPWMType class="btn-ipwm-type" />
          </div>
        </Section>   
      
      </div>
    
      <div class="col-md-6 border border-dark" style="background-color:lavender;">
    
        <Section>
          <h2 class="font-weight-bold text-center">Experiment recommendations</h2>
          <div>
            <p class="lead numbered-paragraph">1. Set Manual PWM mode.</p>
            <p class="lead numbered-paragraph">2. Set desired  PWM mode.</p>
            <p class="lead numbered-paragraph">3. Set initial value of PWM duty cycle.</p>
            <p class="lead numbered-paragraph">4. Add point to "Output voltage vs PWM" chart.</p>
            <p class="lead numbered-paragraph">5. Increase the level of PWM duty cycle.</p>
            <p class="lead numbered-paragraph">6. Repeat 4 and 5 until PWM duty cycle 100%.</p>
            <p class="lead numbered-paragraph">7. Save "Output voltage vs PWM" chart.</p>
          </div>
        </Section>
      </div>

    </div>

    <div class="row">
      <div class="col-md-6 border border-dark" style="background-color:lavender;">
        <Section>
          <h2 class="font-weight-bold text-center">Oscilloscope</h2>
          <ScopeChart style="flex: 1"></ScopeChart>
        </Section>
      </div>

      <div class="col-md-6 border border-dark" style="background-color:lavender;">

        <Section>
          <h2 class="font-weight-bold text-center">Output Voltage vs PWM</h2>
          <VoutGraph />
          <div class="row" align="center">
            <div class="col">
              <button class="btn btn-lg btn-warning"></button>
            </div>
            <div class="col">
              <button class="btn btn-lg btn-warning"></button>
            </div>
            <div class="col">
              <button class="btn btn-lg btn-warning"></button>
            </div>
          </div>
          <div class="row">
            <div class="col">
              <p class="font-italic text-center">Add Point</p>
            </div>
            <div class="col">
              <p class="font-italic text-center">Save Chart</p>
            </div>
            <div class="col">
              <p class="font-italic text-center">Reset Chart</p>
            </div>
          </div>  
        </Section>
      </div>
    </div>
  </div>
</template>

<style>
.input {
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
  display: flex;
  justify-content: center;
  align-items: center;
}
.background {
  background-color: #eef0f6;
  display: flex;
  flex-direction: column;
}

.numbered-paragraph {
  margin: 0px; 
  margin-left: 30px;
}

.img-overlay:before {
  content: ' ';
  display: block;
  height: 50%;
}

.img-overlay {
  position: absolute;
  top: 0;
  bottom: 25;
  left: 0;
  right: 0;
  text-align: center;
}

.img-wrapper {
  position: relative;
}


/* Make the image responsive */
.container-overwritten img {
  width: 100%;
  height: auto;
}

.container-overwritten .btn-vin {
  position: absolute;
  top: 50%;
  left: 10%;
  transform: translate(-50%, -50%);
  -ms-transform: translate(-50%, -50%);
  transform: scale(0.3);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-ipwm {
  position: absolute;
  top: 50%;
  left: 70%;
  transform: translate(-50%, -50%);
  -ms-transform: translate(-50%, -50%);
  transform: scale(0.3);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-ipwm-type {
  position: absolute;
  top: 50%;
  left: 90%;
  transform: translate(-50%, -50%);
  -ms-transform: translate(-50%, -50%);
  transform: scale(0.3);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-iload {
  position: absolute;
  top: 50%;
  left: 30%;
  transform: translate(-50%, -50%);
  -ms-transform: translate(-50%, -50%);
  transform: scale(0.3);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.container-overwritten .btn-icap {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  -ms-transform: translate(-50%, -50%);
  transform: scale(0.3);
  font-size: 16px;
  padding: 1px 1px;
  border: none;
  cursor: pointer;
  border-radius: 1px;
}

</style>
