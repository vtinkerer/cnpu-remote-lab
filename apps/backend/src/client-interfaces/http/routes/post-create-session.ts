import { FastifyPluginAsync } from 'fastify';

import { validateUsernameAndPassword } from '../auth/validate-username-and-password';
import { Static, Type } from '@sinclair/typebox';
import {
  SessionsPostBodyType,
  StartSessionsUsecase,
} from '../../../core/usecases/start-session.usecase';
import { Logger } from '../../../logger/logger';

const responseSchema = Type.Object({
  session_id: Type.String(),
  url: Type.String({
    format: 'uri',
  }),
});

export const postCreateSessionRoute: FastifyPluginAsync = async (
  fastify,
  opts
) => {
  const logger = new Logger(postCreateSessionRoute.name);
  fastify.post<{
    Body: SessionsPostBodyType;
    Reply: Static<typeof responseSchema>;
  }>(
    '/sessions/',
    {
      preHandler: validateUsernameAndPassword,
      schema: {
        response: {
          200: responseSchema,
        },
      },
    },
    async (request, reply) => {
      const usecase = new StartSessionsUsecase(
        fastify.userRepository,
        fastify.clientConnectTimeoutAdapter,
        fastify.config.frontend_url,
        fastify.mcuResetter
      );

      fastify.log.info(`Creating session for ${request.body.user.username}`);
      const { sessionId, url } = await usecase.execute(request.body);

      fastify.log.info(`Session created: ${sessionId}`);

      reply.code(200).send({
        session_id: sessionId,
        url,
      });
    }
  );
};
