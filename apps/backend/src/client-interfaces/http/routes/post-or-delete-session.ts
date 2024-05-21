import { FastifyPluginAsync } from 'fastify';
import { validateUsernameAndPassword } from '../auth/validate-username-and-password';
import { DisposeExperimentUsecase } from '../../../core/usecases/dispose-experiment.usecase';

export const postOrDeleteSessionRoutes: FastifyPluginAsync = async (
  fastify,
  opts
) => {
  fastify.post<{
    Params: { sessionId: string };
  }>(
    '/sessions/:sessionId',
    {
      preHandler: validateUsernameAndPassword,
    },
    async (request, reply) => {
      const { sessionId } = request.params;
      if ((request.body as any)?.action !== 'delete') {
        return reply.code(200).send({
          message: 'Not found',
        });
      }
      const usecase = new DisposeExperimentUsecase(
        fastify.userRepository,
        fastify.clientWebsocketAdapter,
        fastify.clientConnectTimeoutAdapter,
        fastify.clientDisconnectTimeoutAdapter,
        fastify.mcuResetter
      );
      try {
        await usecase.execute({ sessionId, waiting: true });
        return {
          message: 'Deleted',
        };
      } catch (e) {
        return {
          message: 'Not found',
        };
      }
    }
  );

  fastify.delete<{
    Params: { sessionId: string };
  }>(
    '/sessions/:sessionId',
    {
      preHandler: validateUsernameAndPassword,
    },
    async (request, reply) => {
      const { sessionId } = request.params;
      const usecase = new DisposeExperimentUsecase(
        fastify.userRepository,
        fastify.clientWebsocketAdapter,
        fastify.clientConnectTimeoutAdapter,
        fastify.clientDisconnectTimeoutAdapter,
        fastify.mcuResetter
      );
      try {
        await usecase.execute({ sessionId, waiting: true });
        return {
          message: 'Deleted',
        };
      } catch (e) {
        return {
          message: 'Not found',
        };
      }
    }
  );
};
