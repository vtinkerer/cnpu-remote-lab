import { FastifyInstance } from 'fastify';
import { Logger } from '../../logger/logger';
import { AppHttpError } from '../../core/errors/http-error.abstract';

type ErrorHandler = Parameters<FastifyInstance['setErrorHandler']>[0];

export const errorHandler: ErrorHandler = async (err, request, reply) => {
  const logger = new Logger(errorHandler.name);

  if (err instanceof AppHttpError) {
    logger.error({
      isCustom: true,
      ...err,
      stack: err.stack,
    });
    await reply.code(err.statusCode).send({ error: err.message });
    return;
  }

  logger.error({
    message: err.message,
    stack: err.stack,
    name: err.name,
  });
  await reply.status(500).send({ error: err.message });
  return;
};
