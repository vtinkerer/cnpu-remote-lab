import { BaseDto, VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { Logger } from '../../logger/logger';
import { IScopeSender } from '../interfaces/scope-sender.interface';

export class SendMcuDataToUserUsecase {
  private logger = new Logger(SendMcuDataToUserUsecase.name);

  constructor(
    private readonly clientWebsocketAdapter: IClientDataSender,
    private readonly scopeSender: IScopeSender
  ) {}

  async execute<T extends BaseDto>(data: T): Promise<void> {
    if (!this.clientWebsocketAdapter.isAlive()) {
      // this.logger.warn(
      //   "Don't send MCU data because the websocket is not alive"
      // );
      return;
    }
    this.clientWebsocketAdapter.send(data);

    if (data instanceof VoltageOutputDto) {
      this.scopeSender.sendOutVoltage(data.voltage);
    }
  }
}
