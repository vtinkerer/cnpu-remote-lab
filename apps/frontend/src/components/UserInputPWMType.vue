<script setup lang="ts">
import { computed } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { PWMTypeDTO } from '@cnpu-remote-lab-nx/shared';
import { storeToRefs } from 'pinia';

const store = useBackendDataStore();
const { typePWM } = storeToRefs(store);
const isChecked = computed(() => typePWM.value.type === 'MAN');

const handleUserClick = (isChecked: boolean) => {
  store.sendToWebSocket(new PWMTypeDTO({ type: isChecked ? 'MAN' : 'AUT' }));
};
</script>

<template>
  <div>
    <input
      name="checkingbox"
      type="checkbox"
      id="check"
      v-model="isChecked"
      @click="(event) => handleUserClick(event.target.checked)"
    />
    <label for="check" class="button"></label>
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
