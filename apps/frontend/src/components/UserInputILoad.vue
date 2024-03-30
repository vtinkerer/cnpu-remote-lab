<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { CurrentLoad } from '@cnpu-remote-lab-nx/shared';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new CurrentLoad({
      mA: Number(newValue),
    }),
  );
});
</script>

<template>
  <div class="fst-italic" style="font-size: 12px; text-align: center;">
    R<sub>Load</sub>(&Omega;)
    <MyRoundSlider :max="2000" v-model="value" :step="1" />
  </div>
</template>
