<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';
import { CurrentLoadDTO } from '@cnpu-remote-lab-nx/shared';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new CurrentLoadDTO({
      mA: Number(newValue),
    }),
  );
});
</script>

<template>
  <div class="fw-bold fst-italic" style="font-size: 12px; text-align: center">
    I<sub>Load</sub>(mA)
    <MyRoundSlider :max="3000" v-model="value" :step="1" />
  </div>
</template>
