import { BaseDto, VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { Logger } from '../../logger/logger';
import { IScopeSender } from '../interfaces/scope-sender.interface';
import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';

export class SendMcuDataToUserUsecase {
  private logger = new Logger(SendMcuDataToUserUsecase.name);

  constructor(
    private readonly clientWebsocketAdapter: IClientDataSender,
    private readonly scopeSender: IScopeSender,
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async execute<T extends BaseDto>(data: T): Promise<void> {
    if (data instanceof VoltageOutputDto) {
      this.scopeSender.sendOutVoltage(data.voltage);
    }

    this.measurementsRepository.saveMeasurements(data);

    if (this.clientWebsocketAdapter.isAlive()) {
      this.clientWebsocketAdapter.send(data);
    }
  }
}
