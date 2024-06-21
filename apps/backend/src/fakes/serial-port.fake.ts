import EventEmitter from 'node:events';
import { IMcuReceiver } from '../client-interfaces/mcu/mcu.plugin';
import { IMcuSender } from '../core/interfaces/mcu-sender.interface';
import { Logger } from '../logger/logger';
import {
  isPWMTypeDto,
  PWMDTO,
  PWMTypeDTO,
  isLoadTypeDto,
  LoadTypeDTO,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { IMcuResetter } from '../core/interfaces/mcu-resetter.interface';

export function createFakeSerialPort(logger: Logger): {
  receiver: IMcuReceiver;
  sender: IMcuSender;
  resetter: IMcuResetter;
} {
  const events = new EventEmitter();

  setInterval(() => {
    const PWM = Math.floor(Math.random() * 100);
    const Vin = Math.floor(Math.random() * 24);
    const Vout = Math.floor(Math.random() * 24);

    events.emit('data', new VoltageInputDTO({ voltage: Vin }));
    events.emit(
      'data',
      new PWMDTO({
        pwmPercentage: PWM,
      })
    );
    events.emit(
      'data',
      new VoltageOutputDto({
        voltage: Vout,
      })
    );
  }, 1500);

  return {
    receiver: {
      on: events.on.bind(events),
    },
    sender: {
      send: async (data: any) => {
        if (isPWMTypeDto(data)) {
          events.emit(
            'data',
            new PWMTypeDTO({
              type: data.type,
            })
          );
        }
        if (isLoadTypeDto(data)) {
          events.emit(
            'data',
            new LoadTypeDTO({
              type: data.type,
            })
          );
        }
        logger.info({
          message: 'Fake serialport send data',
          data,
        });
      },
    },
    resetter: {
      reset: async () => {
        logger.info({
          message: 'Fake serialport reset',
        });
      },
    },
  };
}
