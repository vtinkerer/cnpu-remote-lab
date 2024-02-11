<script setup lang="ts">
import { useBackendDataStore } from '../stores/back-end-data';

const store = useBackendDataStore();
</script>

<template>
  <div>PWM = {{ store.realPWMDC }}</div>
</template>
