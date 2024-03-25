import EventEmitter from 'node:events';
import { IMcuReceiver } from '../client-interfaces/mcu/mcu.plugin';
import { IMcuSender } from '../core/interfaces/mcu-sender.interface';
import { Logger } from '../logger/logger';
import { PWMReal, VoltageInputReal } from '@cnpu-remote-lab-nx/shared';

export function createFakeSerialPort(logger: Logger): {
  receiver: IMcuReceiver;
  sender: IMcuSender;
} {
  const events = new EventEmitter();

  setInterval(() => {
    const PWM = Math.floor(Math.random() * 100);
    const Vin = Math.floor(Math.random() * 24);

    events.emit('data', new VoltageInputReal({ voltage: Vin }));
    events.emit(
      'data',
      new PWMReal({
        pwmPercentage: PWM,
      })
    );
  }, 1500);

  return {
    receiver: {
      on: events.on.bind(events),
    },
    sender: {
      send: async (data: any) => {
        logger.info({
          message: 'Fake serialport send data',
          data,
        });
      },
    },
  };
}
