import {
  CapacitorReal,
  ClientToServerDTO,
  CurrentLoadReal,
  PWMReal,
  ServerToClientDTO,
  VoltageInputReal,
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
    if (key === 'Vout') {
      return new VoltageOutputDto({ voltage: parseFloat(value) });
    }

    if (key === 'Vin') {
      return new VoltageInputReal({ voltage: parseFloat(value) });
    }

    if (key === 'Iload') {
      return new CurrentLoadReal({ mA: parseFloat(value) });
    }

    if (key === 'Cf') {
      return new CapacitorReal({ capacity: parseFloat(value) });
    }

    if (key === 'PWMDC') {
      return new PWMReal({ pwmPercentage: parseFloat(value) });
    }

    this.logger.warn(`Unknown key: ${key}`);
    return null;
  }
}
