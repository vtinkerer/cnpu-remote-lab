import { ref } from 'vue';
import { defineStore } from 'pinia';
import { getInitState } from '../api/get-init-state.api';
import router from '../router/index';
import {
  isCapacitorRealDto,
  isCurrentLoadRealDto,
  isPWMRealDto,
  isScopeDataDto,
  isSessionIsOverDto,
  isVoltageInputRealDto,
} from '@cnpu-remote-lab-nx/shared';
import type { ClientToServerDTO, ScopeData } from '@cnpu-remote-lab-nx/shared';
import { DateTime, Duration } from 'luxon';

export const useBackendDataStore = defineStore('backend-data', () => {
  const websocket = ref<WebSocket | null>(null);
  const sessionId = ref('');

  const scopeData = ref<ScopeData>([]);
  const realVin = ref(0);
  const realIload = ref(0);
  const realCf = ref(0);
  const realPWMDC = ref(0);
  function connectToWebSocket() {
    if (!sessionId.value) {
      throw new Error('Session ID not provided');
    }
    const ws = new WebSocket(
      import.meta.env.VITE_USE_OVERRIDE_HOSTS?.toLowerCase() === 'true'
        ? `ws://${import.meta.env.VITE_BACKEND_HOST}/ws/create-connection?session-id=${
            sessionId.value
          }`
        : `ws://${window.location.host}/ws/create-connection?session-id=${sessionId.value}`,
    );
    websocket.value = ws;
    ws.onmessage = (event) => {
      const dto = JSON.parse(event.data);

      if (isSessionIsOverDto(dto)) {
        window.location.href = dto.backUrl;
        return;
      }

      if (isScopeDataDto(dto)) {
        scopeData.value = dto.scopeData;
        return;
      }

      if (isVoltageInputRealDto(dto)) {
        realVin.value = dto.voltage;
        return;
      }

      if (isCapacitorRealDto(dto)) {
        realCf.value = dto.capacity;
        return;
      }

      if (isCurrentLoadRealDto(dto)) {
        realIload.value = dto.mA;
        return;
      }

      if (isPWMRealDto(dto)) {
        realPWMDC.value = dto.pwmPercentage;
        return;
      }
    };
  }

  function sendToWebSocket(dto: ClientToServerDTO) {
    if (!websocket.value) {
      console.warn('Websocket not connected, but tried to send message.');
      return;
    }
    console.log('sending to websocket', dto);
    websocket.value.send(JSON.stringify(dto));
  }

  function setSessionId(id: string) {
    sessionId.value = id;
  }

  const timeLeft = ref('');
  async function getIsActive() {
    const data = await getInitState(sessionId.value);
    if (!data.isActive) {
      if (data.url) window.location.href = data.url;
      router.push({ path: '/unknown-user' });
      return;
    }
    const stopTimestamp = DateTime.fromISO(data.stopDate!).toMillis();
    const calculateTimeLeft = () => {
      const millisLeft = stopTimestamp - DateTime.now().toMillis();
      const duration = Duration.fromMillis(millisLeft);
      timeLeft.value = duration.toFormat('hh:mm:ss');
    };
    calculateTimeLeft();
    setInterval(calculateTimeLeft, 1000);
  }

  return {
    connectToWebSocket,
    setSessionId,
    getIsActive,
    sendToWebSocket,
    scopeData,
    realVin,
    realIload,
    realCf,
    realPWMDC,
    timeLeft,
  };
});
