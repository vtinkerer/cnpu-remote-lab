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
import { IMcuSender } from '../interfaces/mcu-sender.interface';
import { IMcuResetter } from '../interfaces/mcu-resetter.interface';
import { Logger } from '../../logger/logger';

export class McuResetter implements IMcuResetter {
  private logger = new Logger(McuResetter.name);

  constructor(private readonly mcuSender: IMcuSender) {}

  async reset(): Promise<void> {
    this.logger.info({
      message: 'Resetting MCU',
    });

    await this.mcuSender.send([
      new PWMDTO({
        pwmPercentage: 0,
      }),
      new VoltageInputDTO({
        voltage: 3,
      }),
      new VoltageOutputDto({
        voltage: 0,
      }),
      new CurrentLoadDTO({
        mA: 0,
      }),
      new LoadTypeDTO({
        type: 'CUR',
      }),
      new PWMTypeDTO({
        type: 'MAN',
      }),
      new CapacitorDTO({
        capacity: 44,
      }),
      new ResistanceLoadDTO({
        resistance: 9999.9,
      }),
    ]);
  }
}
