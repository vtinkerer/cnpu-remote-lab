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

// handler for 'Save Waveform' button
const saveAsImage = () => {
  if (!chart) {
    return;
  }
  let a = document.createElement('a');
  a.href = chart.toBase64Image();
  a.download = 'oscilloscope.png';
  a.click();
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
      labels: scopeData.value.time,
      datasets: [
        {
          type: 'line',
          label: 'Voltage',
          borderColor: '#911',
          backgroundColor: '#911',
          data: scopeData.value.voltage,
        },
        {
          type: 'line',
          label: 'Current',
          borderColor: '#3062b3',
          backgroundColor: '#3062b3',
          data: scopeData.value.current,
          yAxisID: 'yRight',
        },
        {
          type: 'line',
          label: 'PWM',
          borderColor: '#107223',
          backgroundColor: '#107223',
          data: scopeData.value.pwm,
          yAxisID: 'yRight2',
        },
      ],
    },
    options: {
      elements: {
        point: {
          radius: 0,
        },
      },

      maintainAspectRatio: false,
      responsive: true,

      scales: {
        x: {
          title: {
            display: true,
            text: 'Time, us',
            color: '#3062b3',
          },
        },
        y: {
          title: {
            display: true,
            text: 'Voltage, V',
            color: '#911',
          },
        },
        yRight: {
          title: {
            display: true,
            text: 'Current, A',
            color: '#3062b3',
          },
          position: 'right',
        },
        yRight2: {
          position: 'right',
          title: {
            display: true,
            text: 'PWM',
            color: '#107223',
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

// needed for making output image non-transparent
Chart.register({
  id: 'customBckgnd',
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

watch(scopeData, (n) => {
  if (isRender.value) {
    renderScope();
  }
});
</script>

<template>
  <div class="scope-chart">
  <div class="text-scope-chart">
    <div class="relative-scope-chart">
      <canvas ref="chartRef"></canvas>
    </div>

    <div class="row" align="center">
      <div class="col">
        <button
          class="btn btn-md btn-primary"
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
      <div class="col">
        <button class="btn btn-md btn-primary" @click="saveAsImage">Save Waveform</button>
      </div>
    </div>
  </div>
  </div>
</template>

<style>
@import '../style/styles.css';
</style>
