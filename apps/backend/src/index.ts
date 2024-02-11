import { Logger } from './logger/logger';
import { buildApp } from './fastify/server';
import EventEmitter from 'node:events';
import { ScopeData } from '@cnpu-remote-lab-nx/shared';

async function main() {
  const fakeScopeEvents = new EventEmitter();

  setInterval(() => {
    const data: ScopeData = [
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
    ];
    fakeScopeEvents.emit('scope-data', data);
  }, 1000);

  // const server = buildApp({
  //   overrides: {
  //     scope: {
  //       reader: {
  //         on: fakeScopeEvents.on.bind(fakeScopeEvents),
  //         once: fakeScopeEvents.once.bind(fakeScopeEvents),
  //       },
  //     },
  //   },
  // });
  const server = buildApp({});
  server.listen({ port: 3000, host: '0.0.0.0' }, (err, address) => {
    const logger = new Logger(main.name);
    if (err) {
      logger.error(err);
      process.exit(1);
    }
    logger.info(`Server listening at ${address}`);
  });
}

main();
