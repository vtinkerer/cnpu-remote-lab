<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { PWMType } from '@cnpu-remote-lab-nx/shared';

const value = ref('manual');
const store = useBackendDataStore();

watch(value, (newValue) => {
  store.sendToWebSocket(
    new PWMType({
      pwmType: newValue as any,
    }),
  );
});
</script>

<template>
  <div>
    PMWType=
    <select v-model="value">
      <option value="manual">Manual</option>
      <option value="auto">Auto</option>
    </select>
  </div>
</template>
