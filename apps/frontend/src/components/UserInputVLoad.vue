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
  <div class="fw-bold fst-italic" style="font-size: 12px; text-align: center">
    V<sub>Load</sub>(V)
    <MyRoundSlider :max="20" v-model="value" :step="1" />
  </div>
</template>
