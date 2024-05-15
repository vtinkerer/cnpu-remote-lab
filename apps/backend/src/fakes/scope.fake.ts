import { ScopeData } from '@cnpu-remote-lab-nx/shared';
import EventEmitter from 'node:events';
import { IScopeReader } from '../client-interfaces/scope/scope.plugin';

export function createFakeScope(): IScopeReader {
  const fakeScopeEvents = new EventEmitter();

  setInterval(() => {
    const data: ScopeData = {
      voltage: [
        { t: '1s', v: 10 + Math.random() * 2 },
        { t: '2s', v: 20 + Math.random() * 2 },
        { t: '3s', v: 30 + Math.random() * 2 },
        { t: '4s', v: 40 + Math.random() * 2 },
        { t: '5s', v: 50 + Math.random() * 2 },
        { t: '6s', v: 60 + Math.random() * 2 },
        { t: '7s', v: 70 + Math.random() * 2 },
        { t: '8s', v: 80 + Math.random() * 2 },
        { t: '9s', v: 90 + Math.random() * 2 },
        { t: '10s', v: 100 + Math.random() * 2 },
        { t: '11s', v: 90 + Math.random() * 2 },
        { t: '12s', v: 80 + Math.random() * 2 },
        { t: '13s', v: 70 + Math.random() * 2 },
        { t: '14s', v: 60 + Math.random() * 2 },
        { t: '15s', v: 50 + Math.random() * 2 },
        { t: '16s', v: 40 + Math.random() * 2 },
        { t: '17s', v: 30 + Math.random() * 2 },
        { t: '18s', v: 20 + Math.random() * 2 },
        { t: '19s', v: 10 + Math.random() * 2 },
        { t: '20s', v: 0 + Math.random() * 2 },
      ],
    };
    fakeScopeEvents.emit('scope-data', data);
  }, 1000);

  return {
    on: fakeScopeEvents.on.bind(fakeScopeEvents),
    once: fakeScopeEvents.once.bind(fakeScopeEvents),
  };
}
