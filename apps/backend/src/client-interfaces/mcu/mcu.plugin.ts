import fp from 'fastify-plugin';
import {
  CapacitorDTO,
  CurrentLoadDTO,
  LoadTypeDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { IMcuSender } from '../../core/interfaces/mcu-sender.interface';
import { McuReceiver } from './mcu-receiver';
import { McuSender } from '../../adapters/mcu/mcu.adapter';
import { DelimiterParser, SerialPort } from 'serialport';
import { SendMcuDataToUserUsecase } from '../../core/usecases/send-mcu-data-to-user.usecase';
import { createFakeSerialPort } from '../../fakes/serial-port.fake';
import { McuResetter } from '../../core/shared/mcu-resetter';
import { IMcuResetter } from '../../core/interfaces/mcu-resetter.interface';

export type McuMessage =
  | VoltageOutputDto
  | PWMDTO
  | CapacitorDTO
  | CurrentLoadDTO
  | ResistanceLoadDTO
  | PWMTypeDTO
  | LoadTypeDTO;

export interface IMcuReceiver {
  on(event: 'data', listener: (data: McuMessage) => void): void;
  on(event: 'error', listener: (error: Error) => void): void;
}

export const mcuPlugin = () =>
  fp(async (fastify, ops) => {
    const logger = new Logger('mcuPlugin');

    let mcuReceiver: IMcuReceiver;
    let mcuSender: IMcuSender;
    let mcuResetter: IMcuResetter;

    if (!fastify.config.is_fake_serial_port) {
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
      serialPort.on('finish', () => {
        logger.warn('Serialport finished');
      });
      serialPort.on('close', () => {
        logger.error('Serialport closed');
        process.exit(1);
      });
      serialPort.on('drain', () => {
        logger.warn('Serialport drained');
      });
      serialPort.on('end', () => {
        logger.warn('Serialport ended');
      });
      serialPort.on('pipe', () => {
        logger.warn('Serialport piped');
      });
      serialPort.on('unpipe', () => {
        logger.warn('Serialport unpiped');
      });
      const parser = serialPort.pipe(new DelimiterParser({ delimiter: ';' }));
      mcuReceiver = new McuReceiver(parser);
      mcuResetter = new McuResetter(
        mcuSender,
        fastify.config.use_reset_command
      );
    } else {
      const fakes = createFakeSerialPort(logger);
      mcuReceiver = fakes.receiver;
      mcuSender = fakes.sender;
      mcuResetter = fakes.resetter;
    }

    mcuReceiver.on('data', (data) => {
      if (fastify.config.log_messages_from_mcu)
        logger.info(`Received data from MCU: ${JSON.stringify(data)}`);
      new SendMcuDataToUserUsecase(
        fastify.clientWebsocketAdapter,
        fastify.scopeSender
      ).execute(data);
    });

    mcuReceiver.on('error', (error) => {
      logger.error(`Error in MCU: ${error.message}`);
    });

    fastify.decorate('mcuSender', {
      getter() {
        return mcuSender;
      },
    });

    fastify.decorate('mcuResetter', {
      getter() {
        return mcuResetter;
      },
    });
  });
