import fp from 'fastify-plugin';
import {
  CapacitorReal,
  CurrentLoadReal,
  PWMReal,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { IMcuSender } from '../../core/interfaces/mcu-sender.interface';
import { McuReceiver } from './mcu-receiver';
import { McuSender } from '../../adapters/mcu/mcu.adapter';
import { DelimiterParser, SerialPort } from 'serialport';
import { SendMcuDataToUserUsecase } from '../../core/usecases/send-mcu-data-to-user.usecase';

export type McuMessage =
  | VoltageOutputDto
  | PWMReal
  | CapacitorReal
  | CurrentLoadReal;

export interface IMcuReceiver {
  on(event: 'data', listener: (data: McuMessage) => void): void;
  on(event: 'error', listener: (error: Error) => void): void;
}

export const mcuPlugin = (overrides?: {
  sender: IMcuSender;
  receiver: IMcuReceiver;
}) =>
  fp(async (fastify, ops) => {
    const logger = new Logger('mcuPlugin');

    let mcuReceiver = overrides?.receiver;
    let mcuSender = overrides?.sender;

    if (!overrides) {
      // TODO: Create SerialPort connection here
      const serialPort = new SerialPort({
        baudRate: fastify.config.baud_rate,
        path: fastify.config.serial_port_file_path,
      });
      mcuSender = new McuSender(serialPort);

      logger.info('No overrides, starting serialport...');
      serialPort.on('error', (error) => {
        logger.error(`Error during initializing serialport: ${error.message}`);
        process.exit(1);
      });
      const parser = serialPort.pipe(new DelimiterParser({ delimiter: ';' }));
      mcuReceiver = new McuReceiver(parser);
    }

    mcuReceiver.on('data', (data) => {
      logger.info(`Received data from MCU: ${JSON.stringify(data)}`);
      new SendMcuDataToUserUsecase(fastify.clientWebsocketAdapter).execute(
        data
      );
    });

    mcuReceiver.on('error', (error) => {
      logger.error(`Error in MCU: ${error.message}`);
    });

    fastify.decorate('mcuSender', {
      getter() {
        return mcuSender;
      },
    });
  });
