import {
  CurrentLoadDTO,
  PWMDTO,
  ServerToClientDTO,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import { McuMessage } from './mcu.plugin';

export class McuDeserializer {
  private logger = new Logger(McuDeserializer.name);

  private regex = /^([a-zA-Z0-9]+)=([a-zA-Z0-9\.]+)$/;

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
      return;
    }

    if (key === 'C') {
    }

    if (key === 'ERROR') {
    }

    if (key === 'MODE') {
    }

    if (key === 'LOAD') {
    }

    this.logger.warn(`Unknown key: ${key}`);
    return null;
  }
}
