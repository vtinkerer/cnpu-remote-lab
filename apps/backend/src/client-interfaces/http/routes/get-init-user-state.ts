import { Static, Type } from '@sinclair/typebox';
import { FastifyPluginAsync } from 'fastify';
import { GetUserInitState } from '../../../core/usecases/get-user-init-state.usecase';

const paramSchema = Type.Object({
  sessionId: Type.String(),
});

type ParamType = Static<typeof paramSchema>;

export const getInitUserState: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get<{ Params: ParamType }>(
    '/sessions/init-state/:sessionId',
    {
      schema: {
        params: paramSchema,
      },
    },
    async (request, reply) => {
      const { sessionId } = request.params;
      const { isActive, url } = await new GetUserInitState(
        fastify.userRepository
      ).execute(sessionId);
      if (isActive) {
        await reply.status(200).send({ isActive });
        return;
      }
      await reply.status(200).send({ isActive, url });
      return;
    }
  );
};
