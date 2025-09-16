import { BaseDto } from '@cnpu-remote-lab-nx/shared';
import { Measurements } from '../entities/measurements.entity';

export interface IMeasurementsRepository {
  saveMeasurements(measurement: BaseDto): void;
  getMeasurements(): Measurements;
}
