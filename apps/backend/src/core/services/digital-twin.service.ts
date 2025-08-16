import {
  CapacitorDTO,
  LoadTypeDTO,
  PWMDTO,
  ResistanceLoadDTO,
  VoltageInputDTO,
} from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { IMcuSender } from '../interfaces/mcu-sender.interface';
import { sleep } from '../../utils/sleep';
import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';

const compareWithAccuracy = (
  value: number,
  expected: number,
  // Default accuracy is 2% for voltage and current measurements
  accuracy: number = 0.02
): boolean => {
  // Compares two number with a given accuracy in percentage
  const diff = Math.abs(value - expected);
  const threshold = Math.abs(expected * accuracy);
  return diff <= threshold;
};

const VOLTAGE_INPUT = 12;
const PWM_PERCENTAGE = 50;
const CAPACITOR_CAPACITY = 44; // uF
const RESISTANCE = 2;
const VOLTAGE_OUTPUT = VOLTAGE_INPUT * (PWM_PERCENTAGE / 100);

const MCU_COMMANDS_TO_SET = [
  new LoadTypeDTO({
    type: 'RES',
  }),
  new VoltageInputDTO({
    voltage: VOLTAGE_INPUT,
  }),
  new PWMDTO({ pwmPercentage: PWM_PERCENTAGE }),
  new CapacitorDTO({
    capacity: CAPACITOR_CAPACITY,
  }),
  new ResistanceLoadDTO({
    resistance: RESISTANCE,
  }),
] as const;

export class DigitalTwinService {
  private logger = new Logger(DigitalTwinService.name);

  constructor(
    private mcuSender: IMcuSender,
    private measurementsRepository: IMeasurementsRepository
  ) {}

  async checkHardwareConditions(): Promise<void> {
    await this.mcuSender.send([...MCU_COMMANDS_TO_SET]);
    await this.checkCircuitParams();
  }

  private async checkCircuitParams(recursionCounter = 0): Promise<void> {
    if (recursionCounter > 5) {
      this.logger.warn('Max recursion reached');
      return;
    }

    await sleep(200); // Wait to allow the MCU to process the commands and digital oscilloscope to capture the data

    const measurements = this.measurementsRepository.getMeasurements();

    const compareCapacity = compareWithAccuracy(
      measurements.circuit_params.c_value,
      CAPACITOR_CAPACITY
    );
    const comparePWM = compareWithAccuracy(
      measurements.circuit_params.pwm_percentage,
      PWM_PERCENTAGE
    );
    const compareResistance = compareWithAccuracy(
      measurements.circuit_params.r_load,
      RESISTANCE
    );
    const compareVin = compareWithAccuracy(
      measurements.circuit_params.vin,
      VOLTAGE_INPUT
    );
    const compareVout = compareWithAccuracy(
      measurements.circuit_params.vout,
      VOLTAGE_OUTPUT
    );
    if (
      !compareCapacity ||
      !comparePWM ||
      !compareResistance ||
      !compareVin ||
      !compareVout
    ) {
      this.logger.warn({
        msg: 'Circuit params do not match expected values',
        circuitParams: measurements.circuit_params,
        compareCapacity,
        comparePWM,
        compareResistance,
        compareVin,
        compareVout,
      });
      return this.checkCircuitParams(recursionCounter + 1);
    }

    this.logger.info({
      msg: 'Circuit params match expected values',
      measurements,
    });
  }
}
