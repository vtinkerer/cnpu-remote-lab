<script setup lang="ts">
import { ref } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { CapacitorDTO } from '@cnpu-remote-lab-nx/shared';

const capacityValues = [44, 66, 91, 113];
let value = capacityValues[0];

// finds out which button was clicked (firstly 44 mkF is selected)
const isClickedCapac3 = ref(false);
const isClickedCapac2 = ref(false);
const isClickedCapac1 = ref(false);
const isClickedCapac0 = ref(true);

const store = useBackendDataStore();

// save value to send further
function refreshCapac(clickedId: String) {
  console.log("clicked id: " + clickedId);
  if (clickedId === 'capac3') {
    value = capacityValues[3];
  } else if (clickedId === 'capac2') {
    value = capacityValues[2];
  } else if (clickedId === 'capac1') {
    value = capacityValues[1];
  } else {
    value = capacityValues[0];
  }
  console.log("value:" + value);
  store.sendToWebSocket(
    new CapacitorDTO({
      capacity: Number(value),
    }),
  );
}

</script>

<template>
  <div >
    <div class="btn-group-vertical center"> 
      <div class="fw-bold fst-italic" style="font-size: 12px; text-align: center">
        C<sub>F</sub>(&micro;F)
      </div>
      
      <div>  
        <button v-bind:class="{'button-nonclicked': !isClickedCapac3, 'button-clicked': isClickedCapac3}"  
        v-on:click ="isClickedCapac3 = true, isClickedCapac2 = false, isClickedCapac1 = false, isClickedCapac0 = false" 
        @click="refreshCapac('capac3')" id="capac3"> {{capacityValues[3]}} </button>
      </div>

      <div>  
        <button v-bind:class="{'button-nonclicked': !isClickedCapac2, 'button-clicked': isClickedCapac2}"  
        v-on:click ="isClickedCapac3 = false, isClickedCapac2 = true, isClickedCapac1 = false, isClickedCapac0 = false" 
        @click="refreshCapac('capac2')" id="capac2"> {{capacityValues[2]}} </button>
      </div>

      <div>  
        <button v-bind:class="{'button-nonclicked': !isClickedCapac1, 'button-clicked': isClickedCapac1}"  
        v-on:click ="isClickedCapac3 = false, isClickedCapac2 = false, isClickedCapac1 = true, isClickedCapac0 = false" 
        @click="refreshCapac('capac1')" id="capac1"> {{capacityValues[1]}} </button>
      </div>

      <div>  
        <button v-bind:class="{'button-nonclicked': !isClickedCapac0, 'button-clicked': isClickedCapac0}"  
        v-on:click ="isClickedCapac3 = false, isClickedCapac2 = false, isClickedCapac1 = false, isClickedCapac0 = true" 
        @click="refreshCapac('capac0')" id="capac0"> {{capacityValues[0]}} </button>
      </div>
      
    </div>
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
