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
import { IContextRepository } from '../interfaces/context-repository.interface';
import { IMcuResetter } from '../interfaces/mcu-resetter.interface';

const compareWithAccuracy = (
  value: number,
  expected: number,
  accuracy: number = 0.1
): boolean => {
  // Compares two number with a given accuracy in percentage
  const diff = Math.abs(value - expected);
  const threshold = Math.abs(expected * accuracy);
  return diff <= threshold;
};

const VOLTAGE_INPUT = 12;
const PWM_PERCENTAGE = 50;
const CAPACITOR_CAPACITY = 44; // uF
const RESISTANCE = 4;
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
    private readonly mcuSender: IMcuSender,
    private readonly measurementsRepository: IMeasurementsRepository,
    private readonly contextRepository: IContextRepository,
    private readonly mcuResetter: IMcuResetter
  ) {}

  async checkHardwareConditions(): Promise<void> {
    const isOk = await this.checkCircuitParams();
    this.contextRepository.setIsConditionsOk(isOk);
  }

  private async checkCircuitParams(recursionCounter = 0): Promise<boolean> {
    if (recursionCounter > 5) {
      this.logger.warn('Max recursion reached');
      return false;
    }

    await this.mcuResetter.reset();
    await sleep(300);
    await this.mcuSender.send([...MCU_COMMANDS_TO_SET]);
    await sleep(300);

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

    return true;
  }
}
