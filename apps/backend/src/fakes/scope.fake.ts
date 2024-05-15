import { ScopeData } from '@cnpu-remote-lab-nx/shared';
import EventEmitter from 'node:events';
import { IScopeReader } from '../client-interfaces/scope/scope.plugin';

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
        '1s',
        '2s',
        '3s',
        '4s',
        '5s',
        '6s',
        '7s',
        '8s',
        '9s',
        '10s',
        '11s',
        '12s',
        '13s',
        '14s',
        '15s',
        '16s',
        '17s',
        '18s',
        '19s',
        '20s',
      ],
    };
    fakeScopeEvents.emit('scope-data', data);
  }, 1000);

  return {
    on: fakeScopeEvents.on.bind(fakeScopeEvents),
    once: fakeScopeEvents.once.bind(fakeScopeEvents),
  };
}
