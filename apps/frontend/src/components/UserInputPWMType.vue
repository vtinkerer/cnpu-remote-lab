<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import { PWMTypeDTO } from '@cnpu-remote-lab-nx/shared';

const isChecked = ref(false);
const store = useBackendDataStore();

watch(isChecked, (isChecked) => {
  console.log(isChecked);
  if (isChecked) {
    console.log('typePWM:' + store.typePWM.type);
    store.sendToWebSocket(
      new PWMTypeDTO({
        type: 'MAN',
      }),
    );
    store.typePWM.type = 'MAN';
  } else {
    console.log('typePWM:' + store.typePWM.type);
    store.sendToWebSocket(
      new PWMTypeDTO({
        type: 'AUT',
      }),
    );
    store.typePWM.type = 'AUT';
  }
});
</script>

<template>
  <div>
    <input name="checkingbox" type="checkbox" id="check" v-model="isChecked" />
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
  background-color: blue;
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
