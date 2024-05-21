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

export class McuResetter implements IMcuResetter {
  constructor(private readonly mcuSender: IMcuSender) {}

  async reset(): Promise<void> {
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
