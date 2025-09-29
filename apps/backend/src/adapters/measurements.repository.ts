import {
  isCurrentLoadDto,
  isCapacitorDto,
  isPWMDto,
  isVoltageInputDto,
  ScopeData,
  isScopeDataDto,
  BaseDto,
  isResistanceLoadDto,
  VoltageOutputDto,
  isVoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { IMeasurementsRepository } from '../core/interfaces/measurements-repository.interface';
import { Logger } from '../logger/logger';

export class MeasurementsRepository implements IMeasurementsRepository {
  private logger = new Logger(MeasurementsRepository.name);

  private vin: number;
  private pwm_percentage: number;
  private c_value: number;
  private current_out: number;
  private r_load: number;
  private scopeData: ScopeData;
  private vout: number;

  saveMeasurements(measurement: BaseDto): void {
    if (isVoltageInputDto(measurement)) {
      this.vin = measurement.voltage;
    } else if (isPWMDto(measurement)) {
      this.pwm_percentage = measurement.pwmPercentage;
    } else if (isCapacitorDto(measurement)) {
      this.c_value = measurement.capacity;
    } else if (isCurrentLoadDto(measurement)) {
      this.current_out = measurement.mA; // It's an error, it's A not mA
    } else if (isScopeDataDto(measurement)) {
      this.scopeData = measurement.scopeData;
    } else if (isResistanceLoadDto(measurement)) {
      this.r_load = measurement.resistance;
    } else if (isVoltageOutputDto(measurement)) {
      this.vout = measurement.voltage;
    }
    // Otherwise, do nothing
  }

  getMeasurements(): {
    circuit_params: {
      vin: number;
      pwm_percentage: number;
      c_value: number;
      current_out: number;
      r_load: number;
      vout: number;
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
        vin: this.vin,
        pwm_percentage: this.pwm_percentage,
        c_value: this.c_value,
        current_out: this.current_out,
        r_load: this.r_load,
        vout: this.vout,
      },
      measurements: this.scopeData,
    };
  }
}
