import { FastifyPluginAsync } from 'fastify';

export const getSessionsTest: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get('/sessions/test', async (request, reply) => {
    return { valid: true };
  });
};
