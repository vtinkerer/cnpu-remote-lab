import { Logger } from './logger/logger';
import { buildApp } from './fastify/server';

async function main() {
  const server = buildApp();
  server.listen({ port: 3000 }, (err, address) => {
    const logger = new Logger(main.name);
    if (err) {
      logger.error(err);
      process.exit(1);
    }
    logger.info(`Server listening at ${address}`);
  });
}

main();
