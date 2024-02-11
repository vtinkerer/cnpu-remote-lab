import { FastifyPluginAsync } from 'fastify';

export const getApiVersionRoute: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get('/sessions/api', async (request, reply) => {
    return '1';
  });
};
