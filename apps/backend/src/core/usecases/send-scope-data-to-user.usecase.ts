import { ScopeData, ScopeDataDTO } from '@cnpu-remote-lab-nx/shared';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { Logger } from '../../logger/logger';
import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';

export class ProcessScopeDataUsecase {
  private logger = new Logger(ProcessScopeDataUsecase.name);

  constructor(
    private readonly clientWebsocketAdapter: IClientDataSender,
    private readonly measurementRepo: IMeasurementsRepository
  ) {}

  async execute(data: ScopeData): Promise<ScopeDataDTO> {
    const dto = new ScopeDataDTO(data);
    this.measurementRepo.saveMeasurements(dto);
    if (!this.clientWebsocketAdapter.isAlive()) {
      return;
    }
    this.clientWebsocketAdapter.send(dto);
  }
}
