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
  isConditionsOk: Type.Optional(Type.Boolean()),
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
      const { isActive, url, stopDate, isConditionsOk } =
        await new GetUserInitState(
          fastify.userRepository,
          fastify.contextRepository
        ).execute(sessionId);
      if (isActive) {
        await reply
          .status(200)
          .send({ isActive: true, stopDate, url, isConditionsOk });
        return;
      }
      await reply.status(200).send({ isActive: false, url });
      return;
    }
  );
};
