<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
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

const store = useBackendDataStore();

const graphData = ref<{ pwm: number; voltage: number }[]>([]);
const chartRef = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

const addPoint = () => {
  const indexToInsert = graphData.value.findIndex((element) => element.pwm >= store.realPWMDC);

  // If the point already exists, update it
  if (graphData.value[indexToInsert]?.pwm === store.realPWMDC) {
    graphData.value[indexToInsert].voltage = store.realVin;
    return;
  }

  // If there's no point bigger then the current one, push it to the end
  if (indexToInsert === -1) {
    return graphData.value.push({
      pwm: store.realPWMDC,
      voltage: store.realVin,
    });
  }

  // If there's a point bigger than the current one, insert it in the right place and shift all the others
  graphData.value.splice(indexToInsert, 0, {
    pwm: store.realPWMDC,
    voltage: store.realVin,
  });
};

const clearData = () => {
  graphData.value = [];
};

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
      labels: graphData.value.map((val) => val.pwm),
      datasets: [
        {
          type: 'line',
          label: 'Voltage',
          data: graphData.value.map((val) => val.voltage),
          cubicInterpolationMode: 'monotone',
          tension: 0.4,
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

onMounted(() => {
  renderScope();
});

watch(
  graphData,
  () => {
    renderScope();
  },
  { deep: true },
);
</script>

<template>
  <div style="text-align: center">
    <div style="position: relative; height: 40vh; width: 40vw; margin: auto">
      <canvas ref="chartRef"></canvas>
    </div>
    <button @click="addPoint">Add PWM={{ store.realPWMDC }}, Vin={{ store.realVin }}</button>
    <button @click="clearData">Clear</button>
  </div>
</template>
