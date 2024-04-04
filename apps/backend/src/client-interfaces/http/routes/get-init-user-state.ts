import { Static, Type } from '@sinclair/typebox';
import { FastifyPluginAsync } from 'fastify';
import { GetUserInitState } from '../../../core/usecases/get-user-init-state.usecase';

const paramSchema = Type.Object({
  sessionId: Type.String(),
});
type ParamType = Static<typeof paramSchema>;

const responseSchema = Type.Object({
  isActive: Type.Boolean(),
  url: Type.Optional(Type.String()),
  stopDate: Type.Optional(Type.String()),
});
type ResponseType = Static<typeof responseSchema>;

export const getInitUserState: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get<{ Params: ParamType; Reply: ResponseType }>(
    '/sessions/init-state/:sessionId',
    {
      schema: {
        params: paramSchema,
        response: {
          '2xx': responseSchema,
        },
      },
    },
    async (request, reply) => {
      const { sessionId } = request.params;
      const { isActive, url, stopDate } = await new GetUserInitState(
        fastify.userRepository
      ).execute(sessionId);
      if (isActive) {
        await reply.status(200).send({ isActive: true, stopDate, url });
        return;
      }
      await reply.status(200).send({ isActive: false, url });
      return;
    }
  );
};
