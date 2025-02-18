import { FastifyPluginAsync } from 'fastify';

export const testDefectDetector: FastifyPluginAsync = async (fastify, ops) => {
  fastify.post('/test-defect-detector', async (request, reply) => {
    const result = await fastify.defectDetectorAdapter.analyzeMeasurements();
    return reply.status(200).send(result);
  });
};
