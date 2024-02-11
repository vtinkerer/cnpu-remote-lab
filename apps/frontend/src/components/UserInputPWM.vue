<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { PWM } from '@cnpu-remote-lab-nx/shared';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new PWM({
      pwmPercentage: newValue,
    }),
  );
});
</script>

<template>
  <div style="display: flex; flex-direction: column">
    PWM (%)
    <MyRoundSlider :max="100" v-model="value" :step="1" />
  </div>
</template>
