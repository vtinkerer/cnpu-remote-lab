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
  <div style="display: flex; flex-direction: column">
    Vin (V)
    <MyRoundSlider :max="12" v-model="value" :step="1" />
  </div>
</template>
