import { FastifyPluginAsync } from 'fastify';

export const universalRoutes: FastifyPluginAsync = async (fastify, opts) => {
  fastify.get('/*', async (request, reply) => {
    request.log.info('get universal route');
  });
  fastify.post('/*', async (request, reply) => {
    request.log.info('post universal route');
  });

  fastify.put('/*', async (request, reply) => {
    request.log.info('put universal route');
  });

  fastify.delete('/*', async (request, reply) => {
    request.log.info('delete universal route');
  });

  fastify.patch('/*', async (request, reply) => {
    request.log.info('patch universal route');
  });

  fastify.options('/*', async (request, reply) => {
    request.log.info('options universal route');
  });

  fastify.head('/*', async (request, reply) => {
    request.log.info('head universal route');
  });
};
