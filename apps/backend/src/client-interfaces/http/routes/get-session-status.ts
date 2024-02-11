import { FastifyPluginAsync } from 'fastify';
import { validateUsernameAndPassword } from '../auth/validate-username-and-password';
import { GetSessionStatusUsecase } from '../../../core/usecases/get-session-status.usecase';

export const getSessionStatus: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get<{ Params: { sessionId: string } }>(
    '/sessions/:sessionId/status',
    { preHandler: validateUsernameAndPassword },
    async (request, reply) => {
      const sessionId = request.params.sessionId;
      const usecase = new GetSessionStatusUsecase(
        fastify.userRepository,
        fastify.config.weblab_poll_interval_seconds,
        fastify.config.weblab_timeout_seconds
      );
      const res = await usecase.execute(sessionId);

      return {
        should_finish: res,
      };
    }
  );
};
