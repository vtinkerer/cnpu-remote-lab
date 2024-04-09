import {
  CapacitorDTO,
  CurrentLoadDTO,
  LoadTypeDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  ServerToClientDTO,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { McuMessage } from './mcu.plugin';

export class McuDeserializer {
  private logger = new Logger(McuDeserializer.name);

  private regex = /^([a-zA-Z0-9]+)=([a-zA-Z0-9\.]+)$/;

  /**
   *
   * @returns DTO to send or null if there's nothing to send
   */
  deserialize(data: string): McuMessage {
    const matches = this.regex.exec(data);
    if (!matches) return null;
    const [, key, value] = matches;

    // Convert the key-value pair to a DTO here
    if (key === 'VOUT') {
      return new VoltageOutputDto({ voltage: parseFloat(value) });
    }

    if (key === 'VIN') {
      return new VoltageInputDTO({ voltage: parseFloat(value) });
    }

    if (key === 'IL') {
      return new CurrentLoadDTO({ mA: parseFloat(value) });
    }

    if (key === 'PWM') {
      return new PWMDTO({ pwmPercentage: parseFloat(value) });
    }

    if (key === 'RL') {
      return new ResistanceLoadDTO({ resistance: parseFloat(value) });
    }

    if (key === 'C') {
      return new CapacitorDTO({ capacity: parseFloat(value) });
    }

    if (key === 'ERR') {
      this.logger.error({
        message: 'Error from MCU',
        error: value,
        original: data,
      });
      return null;
    }

    if (key === 'MODE') {
      if (value !== 'MAN' && value !== 'AUT') {
        this.logger.warn(`Invalid PWM type: ${value}`);
        return null;
      }
      return new PWMTypeDTO({ type: value });
    }

    if (key === 'LOAD') {
      if (value !== 'CUR' && value !== 'RES') {
        this.logger.warn(`Invalid load type: ${value}`);
        return null;
      }
      return new LoadTypeDTO({ type: value });
    }

    this.logger.warn(`Unknown key: ${key} with data: ${data}`);
    return null;
  }
}
