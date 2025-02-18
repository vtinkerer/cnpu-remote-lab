import { ScopeData, ScopeDataDTO } from '@cnpu-remote-lab-nx/shared';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { Logger } from '../../logger/logger';
import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';

export class SendScopeDataToUserUsecase {
  private logger = new Logger(SendScopeDataToUserUsecase.name);

  constructor(
    private readonly clientWebsocketAdapter: IClientDataSender,
    private readonly measurementRepo: IMeasurementsRepository
  ) {}

  async execute(data: ScopeData): Promise<ScopeDataDTO> {
    if (!this.clientWebsocketAdapter.isAlive()) {
      return;
    }
    const dto = new ScopeDataDTO(data);
    this.clientWebsocketAdapter.send(dto);
    this.measurementRepo.saveMeasurements(dto);
  }
}
