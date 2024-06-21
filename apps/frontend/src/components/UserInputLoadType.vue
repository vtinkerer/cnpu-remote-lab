<script setup lang="ts">
import { computed } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { LoadTypeDTO } from '@cnpu-remote-lab-nx/shared';
import { storeToRefs } from 'pinia';

const store = useBackendDataStore();
const { typeLoad } = storeToRefs(store);
const isChecked = computed(() => typeLoad.value.type === 'RES');

const handleUserClick = (isChecked: boolean) => {
  store.sendToWebSocket(new LoadTypeDTO({ type: isChecked ? 'RES' : 'CUR' }));
};
</script>

<template>
  <div>
    <input
      name="checkingbox"
      type="checkbox"
      id="checkLoadType"
      v-model="isChecked"
      @click="(event) => handleUserClick(event.target.checked)"
    />
    <label for="checkLoadType" class="button"></label>
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
