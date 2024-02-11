import { ClientToServerDTO } from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { IMcuSender } from '../interfaces/mcu-sender.interface';

export class SendUserDataToMcuUsecase {
  private logger = new Logger(SendUserDataToMcuUsecase.name);

  constructor(private readonly mcuDataSender: IMcuSender) {}

  async execute(data: ClientToServerDTO): Promise<void> {
    this.mcuDataSender.send(data);
  }
}
