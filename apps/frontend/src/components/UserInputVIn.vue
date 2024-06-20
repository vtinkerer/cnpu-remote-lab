<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { VoltageInputDTO } from '@cnpu-remote-lab-nx/shared';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new VoltageInputDTO({
      voltage: Number(newValue),
    }),
  );
});
</script>

<template>
  <div class="fw-bold fst-italic input-roundslider-label">
    V<sub>in</sub> (V)
    <MyRoundSlider :min="3" :max="21" :step="1"  v-model="value" />
  </div>
</template>

<style> 
@import '../style/styles.css';
</style>
