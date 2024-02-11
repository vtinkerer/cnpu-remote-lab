<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { CapacitorInput } from '@cnpu-remote-lab-nx/shared';
import MyRoundSlider from '../components/RoundSlider/MyRoundSlider.vue';

const value = ref(0);
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new CapacitorInput({
      capacity: Number(newValue),
    }),
  );
});
</script>

<template>
  <div style="display: flex; flex-direction: column">
    Cf (pF)
    <MyRoundSlider :max="1000000" v-model="value" :step="5" />
  </div>
</template>
