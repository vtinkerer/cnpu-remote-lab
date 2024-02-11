import { FastifyPluginAsync } from 'fastify';
import { AuthenticateWsConnectionUsecase } from '../../core/usecases/authenticate-ws-connection.usecase';
import { Logger } from '../../logger/logger';
import { Static, Type } from '@sinclair/typebox';
import { wsHandler } from './websocket-handler';

const querySchema = Type.Object({
  'session-id': Type.String(),
});

type QueryType = Static<typeof querySchema>;

export const createClientWebsocketConnection: FastifyPluginAsync = async (
  fastify,
  opts
) => {
  const logger = new Logger(createClientWebsocketConnection.name);

  fastify.get<{
    Querystring: QueryType;
  }>(
    '/create-connection',
    {
      schema: {
        querystring: querySchema,
      },
      websocket: true,
      preHandler: async (req, res) => {
        logger.info('Got a new connection');
        const sessionId = req.query['session-id'] as string;
        if (!sessionId) {
          logger.info('it does not have a session ID, returning 400');
          return res.status(400).send({ error: 'Session ID not provided' });
        }
        await new AuthenticateWsConnectionUsecase(
          fastify.userRepository
        ).execute(sessionId);
        logger.info('Authenticated');
      },
    },
    wsHandler
  );
};
