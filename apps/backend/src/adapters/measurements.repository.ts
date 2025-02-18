import {
  isCurrentLoadDto,
  isCapacitorDto,
  isPWMDto,
  isVoltageInputDto,
  ScopeData,
  isScopeDataDto,
  BaseDto,
} from '@cnpu-remote-lab-nx/shared';
import { IMeasurementsRepository } from '../core/interfaces/measurements-repository.interface';

export class MeasurementsRepository implements IMeasurementsRepository {
  private Vin: number;
  private duty_cycle: number;
  private c_value: number;
  private current_out: number;
  private scopeData: ScopeData;

  saveMeasurements(measurement: BaseDto): void {
    if (isVoltageInputDto(measurement)) {
      this.Vin = measurement.voltage;
    } else if (isPWMDto(measurement)) {
      this.duty_cycle = Math.round(measurement.pwmPercentage / 100);
    } else if (isCapacitorDto(measurement)) {
      this.c_value = measurement.capacity * 1e-6;
    } else if (isCurrentLoadDto(measurement)) {
      this.current_out = measurement.mA; // It's an error, it's A not mA
    } else if (isScopeDataDto(measurement)) {
      this.scopeData = measurement.scopeData;
    }
    // Otherwise, do nothing
  }

  getMeasurements(): {
    circuit_params: {
      Vin: number;
      duty_cycle: number;
      c_value: number;
      current_out: number;
    };
    measurements: {
      voltage: number[];
      time: number[];
      pwm: number[];
      current: number[];
    };
  } {
    return {
      circuit_params: {
        Vin: this.Vin,
        duty_cycle: this.duty_cycle,
        c_value: this.c_value,
        current_out: this.current_out,
      },
      measurements: this.scopeData,
    };
  }
}
