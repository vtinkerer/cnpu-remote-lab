import { BaseDto } from '@cnpu-remote-lab-nx/shared';

export interface IMeasurementsRepository {
  saveMeasurements(measurement: BaseDto): void;
  getMeasurements(): {
    circuit_params: {
      vin: number;
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
  };
}
