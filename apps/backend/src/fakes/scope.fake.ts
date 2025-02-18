import { ScopeData } from '@cnpu-remote-lab-nx/shared';
import EventEmitter from 'node:events';
import { IScopeReader } from '../client-interfaces/scope/scope.plugin';
import { IScopeSender } from '../core/interfaces/scope-sender.interface';

export function createFakeScope(): IScopeReader {
  const fakeScopeEvents = new EventEmitter();

  setInterval(() => {
    const data: ScopeData = {
      voltage: [
        10 + Math.random() * 2,
        20 + Math.random() * 2,
        30 + Math.random() * 2,
        40 + Math.random() * 2,
        50 + Math.random() * 2,
        60 + Math.random() * 2,
        70 + Math.random() * 2,
        80 + Math.random() * 2,
        90 + Math.random() * 2,
        100 + Math.random() * 2,
        90 + Math.random() * 2,
        80 + Math.random() * 2,
        70 + Math.random() * 2,
        60 + Math.random() * 2,
        50 + Math.random() * 2,
        40 + Math.random() * 2,
        30 + Math.random() * 2,
        20 + Math.random() * 2,
        10 + Math.random() * 2,
        0 + Math.random() * 2,
      ],
      current: [
        1 + Math.random() * 2,
        2 + Math.random() * 2,
        3 + Math.random() * 2,
        4 + Math.random() * 2,
        5 + Math.random() * 2,
        6 + Math.random() * 2,
        7 + Math.random() * 2,
        8 + Math.random() * 2,
        9 + Math.random() * 2,
        10 + Math.random() * 2,
        9 + Math.random() * 2,
        8 + Math.random() * 2,
        7 + Math.random() * 2,
        6 + Math.random() * 2,
        5 + Math.random() * 2,
        4 + Math.random() * 2,
        3 + Math.random() * 2,
        2 + Math.random() * 2,
        1 + Math.random() * 2,
        0 + Math.random() * 2,
      ],
      time: [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
      ],
      pwm: [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    };
    fakeScopeEvents.emit('scope-data', data);
  }, 1000);

  return {
    on: fakeScopeEvents.on.bind(fakeScopeEvents),
    once: fakeScopeEvents.once.bind(fakeScopeEvents),
  };
}

export function createFakeScopeSender(): IScopeSender {
  return {
    sendOutVoltage: (voltage: number) => {
      console.log(`[FAKE] Sending out voltage: ${voltage}`);
    },
  };
}
