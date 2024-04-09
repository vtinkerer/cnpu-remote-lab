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
.button {
  background-color: #d2d2d2;
  width: 20px;
  height: 10px;
  border-radius: 20px;
  cursor: pointer;
  position: relative;
  transition: 0.2s;
}
.button::before {
  position: absolute;
  content: '';
  background-color: #54bbe0;
  width: 9px;
  height: 9px;
  border-radius: 20px;
  margin: 0.5px;
  transition: 0.2s;
}

input:checked + .button {
  background-color: #d2d2d2;
}

input:checked + .button::before {
  transform: translateX(10px);
}

input {
  display: none;
}
</style>
