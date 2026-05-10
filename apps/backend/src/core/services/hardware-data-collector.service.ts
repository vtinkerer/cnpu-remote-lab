import {
  CapacitorDTO,
  LoadType,
  LoadTypeDTO,
  PWMDTO,
  ResistanceLoadDTO,
  VoltageInputDTO,
} from '@cnpu-remote-lab-nx/shared';
import fs from 'node:fs';
import { Logger } from '../../logger/logger';
import { sleep } from '../../utils/sleep';
import { IMcuSender } from '../interfaces/mcu-sender.interface';
import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';

// ───── EDIT THESE TO CHANGE WHAT THE LAB RUNS WITH ─────
const DESIRED_PARAMS = {
  loadType: 'RES' as LoadType,
  voltageInput: 12, // V
  pwmPercentage: 1, // %
  capacitorCapacity: 44, // µF
  resistance: 4, // Ω
};

const INTERVAL_MS = 1000;
const SETTLE_MS = 2000;
const OUTPUT_DIR = '/home/user1-44';
// ───────────────────────────────────────────────────────

const OUTPUT_FILE = `${OUTPUT_DIR}/raw-measurements-with-v-${DESIRED_PARAMS.voltageInput}-pwm-${DESIRED_PARAMS.pwmPercentage}-c-${DESIRED_PARAMS.capacitorCapacity}-r-${DESIRED_PARAMS.resistance}.jsonl`;

export class HardwareDataCollectorService {
  private logger = new Logger(HardwareDataCollectorService.name);
  private timer: NodeJS.Timeout | null = null;

  constructor(
    private readonly mcuSender: IMcuSender,
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async start(): Promise<void> {
    if (this.timer) {
      this.logger.warn('Already running');
      return;
    }

    this.logger.info({
      msg: 'Applying desired circuit params and starting periodic capture',
      params: DESIRED_PARAMS,
      intervalMs: INTERVAL_MS,
      outputFile: OUTPUT_FILE,
    });

    await this.mcuSender.send([
      new LoadTypeDTO({ type: DESIRED_PARAMS.loadType }),
      new VoltageInputDTO({ voltage: DESIRED_PARAMS.voltageInput }),
      new PWMDTO({ pwmPercentage: DESIRED_PARAMS.pwmPercentage }),
      new CapacitorDTO({ capacity: DESIRED_PARAMS.capacitorCapacity }),
      new ResistanceLoadDTO({ resistance: DESIRED_PARAMS.resistance }),
    ]);

    await sleep(SETTLE_MS);

    this.timer = setInterval(() => {
      try {
        const data = this.measurementsRepository.getMeasurements();
        if (!data.measurements) return;
        fs.appendFileSync(OUTPUT_FILE, JSON.stringify(data) + '\n');
      } catch (err) {
        this.logger.error({ msg: 'Failed to write hardware data', err });
      }
    }, INTERVAL_MS);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}
