<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';
import { PWMDTO } from '@cnpu-remote-lab-nx/shared';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new PWMDTO({
      pwmPercentage: newValue,
    }),
  );
});
</script>

<template>
  <div
    class="fw-bold fst-italic"
    style="font-size: 12px; text-align: center; display: flex; flex-direction: column"
  >
    PWM (%)
    <MyRoundSlider :max="100" v-model="value" :step="1" />
  </div>
</template>
