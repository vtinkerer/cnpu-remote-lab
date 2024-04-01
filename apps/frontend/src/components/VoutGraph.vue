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

// handler for 'Add point' button
const addPoint = () => {
  const indexToInsert = graphData.value.findIndex((element) => element.pwm >= store.realPWMDC);
  // If the point already exists, update it
  if (graphData.value[indexToInsert]?.pwm === store.realPWMDC) {
    graphData.value[indexToInsert].voltage = store.VOut;
    return;
  }

  // If there's no point bigger then the current one, push it to the end
  if (indexToInsert === -1) {
    return graphData.value.push({
      pwm: store.realPWMDC,
      voltage: store.VOut,
    });
  }

  // If there's a point bigger than the current one, insert it in the right place and shift all the others
  graphData.value.splice(indexToInsert, 0, {
    pwm: store.realPWMDC,
    voltage: store.VOut,
  });
};

// handler for 'Save chart' button
const saveAsImage = () => {
  if (!chart) {
    return;
  }
  let a = document.createElement('a');
  a.href = chart.toBase64Image();
  a.download = 'buck_v_vs_pwm.png';
  a.click();
};

// handler for 'Reset chart' button
const clearData = () => {
  graphData.value = [];
};

const renderScope = () => {
  const ctx = chartRef.value?.getContext('2d');
  console.log(graphData);
  if (!ctx) {
    return;
  }

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: graphData.value.map((val) => val.pwm),
      datasets: [
        {
          type: 'line',
          label: 'Voltage',
          borderColor: '#3062b3',
          backgroundColor: '#3062b3',
          data: graphData.value.map((val) => val.voltage),
          cubicInterpolationMode: 'monotone',
          tension: 0.4,
        },
      ],
    },
    options: {
      parsing: {
        xAxisKey: 'pwm',
        yAxisKey: 'voltage',
      },
      maintainAspectRatio: false,
      responsive: true,
      scales: {
        x: {
          beginAtZero: true,
          type: 'linear',
          min: 0,
          max: 100,
          ticks: {
            stepSize: 10,
          },
          title: {
            display: true,
            text: 'PWM, %',
            color: '#911',
          },
        },
        y: {
          beginAtZero: true,
          min: 0,
          max: 22,
          ticks: {
            stepSize: 2,
          },
          title: {
            display: true,
            text: 'Voltage, V',
            color: '#3062b3',
          },
        },
      },
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

// needed for making output image non-transparent
Chart.register({
  id: 'customBackground',
  beforeDraw: (chart, args, opts) => {
    const ctx = chart.canvas.getContext('2d');
    if (!ctx) {
      return;
    }
    ctx.save();
    ctx.globalCompositeOperation = 'destination-over';
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  },
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
    <div class="point-info">Point: PWM={{ store.realPWMDC }}, VOut={{ store.VOut }}</div>
  </div>
  <div class="row" align="center">
    <div class="col">
      <p class="btn btn-md btn-primary"@click="addPoint">Add Point</p>
    </div>
    <div class="col">
      <button class="btn btn-md btn-primary"@click="saveAsImage">Save Chart</button>
    </div>
    <div class="col">
      <button class="btn btn-md btn-primary"@click="clearData">Reset Chart</button>
    </div>
  </div>
</template>

<style>
.point-info {
  width: auto;
  padding: 1px;
  margin: 5px;
  border: 1px solid black;
  background-color: white;
}
</style>
