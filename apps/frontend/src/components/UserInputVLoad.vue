<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';
import { VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new VoltageOutputDto({
      voltage: Number(newValue),
    }),
  );
});
</script>

<template>
  <div class="fw-bold fst-italic input-roundslider-label">
    V<sub>Load</sub>(V)
    <MyRoundSlider :min="0" :max="20" :step="1" v-model="value" />
  </div>
</template>

<style> 
@import '../style/styles.css';
</style>
