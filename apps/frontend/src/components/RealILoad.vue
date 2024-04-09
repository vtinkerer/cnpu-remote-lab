<script setup lang="ts">
import { useBackendDataStore } from '../stores/back-end-data';

const store = useBackendDataStore();
</script>

<template>
  <div>{{ store.realIload }}A</div>
</template>
