<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBackendDataStore } from '../stores/back-end-data';
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import { storeToRefs } from 'pinia';

Chart.register(
  BarController,
  LineController,
  CategoryScale,
  LinearScale,
  PointElement,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const isRender = ref(true);
const buttonName = ref<'Start' | 'Pause'>('Pause');

const store = useBackendDataStore();
const { scopeData } = storeToRefs(store);
const chartRef = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

const renderScope = () => {
  const ctx = chartRef.value?.getContext('2d');
  if (!ctx) {
    return;
  }

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(ctx, {
    data: {
      labels: scopeData.value.map((val) => val.t),
      datasets: [
        {
          type: 'line',
          label: 'Voltage',
          borderColor: '#911',
          backgroundColor: '#911',
          data: scopeData.value.map((val) => val.v),
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      responsive: true,
      datasets: {
        line: {
          animation: {
            duration: 0,
          },
        },
      },
    },
  });
};

watch(scopeData, (n) => {
  if (isRender.value) {
    renderScope();
  }
});
</script>

<template>
  <div style="text-align: center">
    <div style="position: relative; height: 40vh; width: 40vw; margin: auto">
      <canvas ref="chartRef"></canvas>
    </div>
    <button
      @click="
        () => {
          isRender = !isRender;
          buttonName = isRender ? 'Pause' : 'Start';
        }
      "
    >
      {{ buttonName }}
    </button>
  </div>
</template>
