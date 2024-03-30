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
  <div class="fst-italic" style="font-size: 12px; text-align: center;">
    C<sub>F</sub> (pF)
    <MyRoundSlider :max="1000000" v-model="value" :step="5" />
  </div>
</template>
