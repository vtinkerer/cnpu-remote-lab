import { ref } from 'vue';
import { defineStore } from 'pinia';
import { getInitState } from '../api/get-init-state.api';
import router from '../router/index';
import {
  isScopeDataDto,
  isSessionIsOverDto,
  isPWMTypeDto,
  isLoadTypeDto,
  isVoltageInputDto,
  isCapacitorDto,
  isCurrentLoadDto,
  isPWMDto,
  isVoltageOutputDto,
  isResistanceLoadDto,
  LaboratoryType,
} from '@cnpu-remote-lab-nx/shared';
import type { BaseDto, ScopeData } from '@cnpu-remote-lab-nx/shared';
import { DateTime, Duration } from 'luxon';

export const useBackendDataStore = defineStore('backend-data', () => {
  const websocket = ref<WebSocket | null>(null);
  const sessionId = ref('');

  const scopeData = ref<ScopeData>({ voltage: [], time: [], current: [], pwm: [] });
  const realVin = ref(0);
  const realIload = ref(0);
  const realCf = ref(0);
  const realPWMDC = ref(0);
  const realRload = ref(0);
  const VOut = ref(0);
  const typeLoad = ref({ type: 'CUR' });
  const typePWM = ref({ type: 'AUT' });
  const laboratoryType = ref(LaboratoryType.UP);

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

      if (isVoltageInputDto(dto)) {
        realVin.value = dto.voltage;
        return;
      }

      if (isCapacitorDto(dto)) {
        realCf.value = dto.capacity;
        return;
      }

      if (isCurrentLoadDto(dto)) {
        realIload.value = dto.mA;
        return;
      }

      if (isResistanceLoadDto(dto)) {
        realRload.value = dto.resistance;
        return;
      }

      if (isPWMDto(dto)) {
        realPWMDC.value = dto.pwmPercentage;
        return;
      }

      if (isVoltageOutputDto(dto)) {
        VOut.value = dto.voltage;
        return;
      }

      if (isPWMTypeDto(dto)) {
        typePWM.value.type = dto.type;
      }

      if (isLoadTypeDto(dto)) {
        typeLoad.value.type = dto.type;
      }

    };
  }

  function sendToWebSocket(dto: BaseDto) {
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

    if (data.laboratoryType === LaboratoryType.UP) {
      laboratoryType.value = LaboratoryType.UP;
    } else {
      laboratoryType.value = LaboratoryType.DOWN;
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
    realRload,
    realCf,
    realPWMDC,
    timeLeft,
    VOut,
    typePWM,
    typeLoad,
    laboratoryType,
  };
});
