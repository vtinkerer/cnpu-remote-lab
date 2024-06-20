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
  <div class="fw-bold fst-italic input-roundslider-label">
    I<sub>Load</sub>(mA)
    <MyRoundSlider :min="0" :max="3000" :step="1" v-model="value" />
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
