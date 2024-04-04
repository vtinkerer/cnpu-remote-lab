import { WebsocketHandler } from '@fastify/websocket';
import { ClientWebsocketConnectUsecase } from '../../core/usecases/client-websocket-connect.usecase';
import { ClientWebsocketDisconnectUsecase } from '../../core/usecases/client-websocket-disconnect.usecase';
import { Logger } from '../../logger/logger';
import {
  CapacitorDTO,
  CurrentLoadDTO,
  LoadTypeDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { SendUserDataToMcuUsecase } from '../../core/usecases/send-user-data-to-mcu.usecase';

const dtoClasses = [
  VoltageInputDTO,
  VoltageOutputDto,
  CurrentLoadDTO,
  CapacitorDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  LoadTypeDTO,
];

export const wsHandler: WebsocketHandler = (connection, req) => {
  const logger = new Logger(wsHandler.name);
  const fastify = req.server;

  try {
    new ClientWebsocketConnectUsecase(
      fastify.clientWebsocketAdapter,
      fastify.clientConnectTimeoutAdapter,
      fastify.clientDisconnectTimeoutAdapter
    ).execute(connection.socket);

    connection.socket.on('close', () => {
      new ClientWebsocketDisconnectUsecase(
        fastify.clientWebsocketAdapter,
        fastify.clientDisconnectTimeoutAdapter
      ).execute();
      logger.info('Connection closed');
    });

    connection.socket.on('message', (message) => {
      logger.info(`Received a message: ${message.toString()}`);
      const dto = JSON.parse(message.toString());

      if (!dto.dtoName) {
        logger.warn('Received a message without a dtoName');
        return;
      }

      const dtoClass = dtoClasses.find(
        (dtoClass) => dtoClass.name === dto.dtoName
      );

      if (!dtoClass) {
        logger.warn('Received a message with an unknown dtoName');
        return;
      }

      new SendUserDataToMcuUsecase(fastify.mcuSender).execute(
        new dtoClass(dto)
      );
    });
  } catch (error) {
    logger.error(
      `Error handling websocket connection: ${error} ${error.stack}`
    );
    connection.socket.close();
  }
};
