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
import { IDefectDetectorAdapter } from '../interfaces/defect-detector-adapter.interface';
import fs from 'node:fs';
import { DefectDetectorAnalysisResult } from '../entities/defect-detector-measurements.entity';
import { Measurements } from '../entities/measurements.entity';

const PARAMETERS_MAPPINGS = {
  '++++': [
    ['+++', '++'],
    ['0'],
    ['---'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '000+': [['+'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '0000': [
    ['-'],
    ['0'],
    ['0'],
    ['++', '+'],
    ['0'],
    ['0'],
    ['+', '-', '--'],
    ['++', '+', '-', '--', '---'],
    ['+', '-', '--', '---'],
  ],
  '----': [
    ['--', '---'],
    ['--', '---'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['+++', '++'],
    ['+++'],
    ['0'],
  ],
  '+-+-': [
    ['0'],
    ['+++', '++'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '+0+0': [['0'], ['+'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '-0-0': [['0'], ['-'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '0-0-': [
    ['0'],
    ['0'],
    ['+++', '++', '+'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '0+0+': [['0'], ['0'], ['-'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '0+++': [['0'], ['0'], ['--'], ['0'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '-+++': [['0'], ['0'], ['0'], ['+++'], ['0'], ['0'], ['0'], ['0'], ['0']],
  '0+00': [
    ['0'],
    ['0'],
    ['0'],
    ['-', '--', '---'],
    ['0'],
    ['+++', '++', '+'],
    ['---'],
    ['0'],
    ['0'],
  ],
  '00-0': [
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['+++', '++', '+'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '00+0': [['0'], ['0'], ['0'], ['0'], ['-'], ['0'], ['0'], ['0'], ['0']],
  '--++': [
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['--', '---'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '0-00': [
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['-', '--', '---'],
    ['0'],
    ['0'],
    ['0'],
  ],
  '-+-+': [
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['0'],
    ['+++', '++'],
  ],
};

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

const V_AVERAGE_THETA = 5; // 5%
const V_RIPPLE_THETA = 75; // 75%
const I_AVERAGE_THETA = 20; // 20%
const I_RIPPLE_THETA = 50; // 50%

type Character = '+' | '0' | '-';
type Vector = `${Character}${Character}${Character}${Character}`;

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

let biggestVmeanError = 0;
let biggestVrippleError = 0;
let biggestImeanError = 0;
let biggestIrippleError = 0;

export class DigitalTwinService {
  private logger = new Logger(DigitalTwinService.name);

  constructor(
    private readonly mcuSender: IMcuSender,
    private readonly measurementsRepository: IMeasurementsRepository,
    private readonly contextRepository: IContextRepository,
    private readonly mcuResetter: IMcuResetter,
    private readonly defectDetectorAdapter: IDefectDetectorAdapter
  ) {}

  async checkHardwareConditions(): Promise<void> {
    const areParamsMet = await this.checkCircuitParams();
    if (!areParamsMet) {
      this.logger.error({
        msg: 'Hardware conditions not met after several retries',
      });
      this.contextRepository.setIsConditionsOk(false);
      return;
    }
    const measurementsAnalyzed =
      await this.defectDetectorAdapter.analyzeMeasurements();
    this.logger.info({
      msg: 'Measurements analyzed',
      analysis: measurementsAnalyzed,
    });

    await this.createFileIfMeasurementsAreOff(measurementsAnalyzed);

    const inputVector = this.calculateTableInputVector(
      measurementsAnalyzed.result
    );
    this.logger.info({ msg: 'Input vector', inputVector });

    const tableResult = this.calculateTableResult(inputVector);
    this.logger.info({ msg: 'Table result', tableResult });

    const condition = inputVector === '0000';

    this.logger.info({
      msg: 'Hardware conditions',
      condition,
    });

    // TODO: Set the actual isOk value
    this.contextRepository.setIsConditionsOk(condition);
  }

  private calculateTableResult(vector: Vector) {
    return PARAMETERS_MAPPINGS[vector];
  }

  private calculateTableInputVector(
    result: DefectDetectorAnalysisResult
  ): Vector {
    const arr: Character[] = [];

    if (result.percentage_difference_avg_vout > V_AVERAGE_THETA) {
      arr.push('+');
    } else if (result.percentage_difference_avg_vout < -V_AVERAGE_THETA) {
      arr.push('-');
    } else {
      arr.push('0');
    }

    if (result.percentage_difference_ripple_vout > V_RIPPLE_THETA) {
      arr.push('+');
    } else if (result.percentage_difference_ripple_vout < -V_RIPPLE_THETA) {
      arr.push('-');
    } else {
      arr.push('0');
    }

    if (result.percentage_difference_avg_il > I_AVERAGE_THETA) {
      arr.push('+');
    } else if (result.percentage_difference_avg_il < -I_AVERAGE_THETA) {
      arr.push('-');
    } else {
      arr.push('0');
    }

    if (result.percentage_difference_ripple_il > I_RIPPLE_THETA) {
      arr.push('+');
    } else if (result.percentage_difference_ripple_il < -I_RIPPLE_THETA) {
      arr.push('-');
    } else {
      arr.push('0');
    }

    return arr.join('') as Vector;
  }

  private async createFileIfMeasurementsAreOff(measurementsAnalyzed: {
    result: DefectDetectorAnalysisResult;
    measurements: Measurements;
  }) {
    const newBiggestVmeanError = Math.max(
      Math.abs(measurementsAnalyzed.result.percentage_difference_avg_vout),
      biggestVmeanError
    );
    const newBiggestVrippleError = Math.max(
      Math.abs(measurementsAnalyzed.result.percentage_difference_ripple_vout),
      biggestVrippleError
    );
    const newBiggestImeanError = Math.max(
      Math.abs(measurementsAnalyzed.result.percentage_difference_avg_il),
      biggestImeanError
    );
    const newBiggestIrippleError = Math.max(
      Math.abs(measurementsAnalyzed.result.percentage_difference_ripple_il),
      biggestIrippleError
    );
    if (
      newBiggestVmeanError > biggestVmeanError ||
      newBiggestVrippleError > biggestVrippleError ||
      newBiggestImeanError > biggestImeanError ||
      newBiggestIrippleError > biggestIrippleError
    ) {
      const vector = [
        measurementsAnalyzed.result.percentage_difference_avg_vout,
        measurementsAnalyzed.result.percentage_difference_ripple_vout,
        measurementsAnalyzed.result.percentage_difference_avg_il,
        measurementsAnalyzed.result.percentage_difference_ripple_il,
      ];
      const vectorString = vector.map((v) => v.toFixed(2)).join(',');
      fs.writeFileSync(
        `/home/user1-44/${new Date().toISOString()}-${vectorString}-measurements.json`,
        JSON.stringify(measurementsAnalyzed.measurements, null, 2)
      );
    }

    biggestVmeanError = newBiggestVmeanError;
    biggestVrippleError = newBiggestVrippleError;
    biggestImeanError = newBiggestImeanError;
    biggestIrippleError = newBiggestIrippleError;

    this.logger.info({
      msg: 'Biggest errors so far',
      biggestVmeanError,
      biggestVrippleError,
      biggestImeanError,
      biggestIrippleError,
    });
  }

  private async _sendCommands() {
    await this.mcuSender.send([...MCU_COMMANDS_TO_SET]);
  }

  private async checkCircuitParams(recursionCounter = 0): Promise<boolean> {
    if (recursionCounter === 0) {
      await this._sendCommands();
    }

    await sleep(500);

    if (recursionCounter > 10) {
      this.logger.warn('Max recursion reached');
      return false;
    }

    const measurements = this.measurementsRepository.getMeasurements();

    this.logger.info({
      msg: 'Checking circuit params',
      params: measurements.circuit_params,
    });

    // Sometimes the scope reader returns constant voltage measurements for some reason
    // This is a workaround to retry the check if the measurements are constant
    const minVoltage = Math.min(...measurements.measurements.voltage);
    const maxVoltage = Math.max(...measurements.measurements.voltage);
    if (minVoltage === maxVoltage) {
      this.logger.info({
        msg: 'Voltage measurements are constant, retrying',
        minVoltage,
        maxVoltage,
      });
      return this.checkCircuitParams(recursionCounter + 1);
    }

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
      await this._sendCommands();
      return this.checkCircuitParams(recursionCounter + 1);
    }

    this.logger.info({
      msg: 'Circuit params match expected values',
    });

    return true;
  }
}
