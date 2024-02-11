import { ScopeData, ScopeDataDTO } from '@cnpu-remote-lab-nx/shared';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { Logger } from '../../logger/logger';

export class SendScopeDataToUserUsecase {
  private logger = new Logger(SendScopeDataToUserUsecase.name);

  constructor(private readonly clientWebsocketAdapter: IClientDataSender) {}

  async execute(data: ScopeData): Promise<void> {
    if (!this.clientWebsocketAdapter.isAlive()) {
      return;
    }
    const dto = new ScopeDataDTO(data);
    this.clientWebsocketAdapter.send(dto);
  }
}
