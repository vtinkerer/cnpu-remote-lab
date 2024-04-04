import { IMcuSender } from '../../core/interfaces/mcu-sender.interface';
import { serializers } from './mcu-serializer';
import { Logger } from '../../logger/logger';

import './serializers/capasitor.serializer';
import './serializers/current.serializer';
import './serializers/input-voltage.serializer';
import './serializers/pwm-duty-cycle.serializer';
import './serializers/pwm-type.serializer';
import './serializers/resistance-load.serializer';
import './serializers/output-voltage.serializer';
import './serializers/load-type.serializer';

import { SerialPort } from 'serialport';
import { BaseDto } from '@cnpu-remote-lab-nx/shared';

export class McuSender implements IMcuSender {
  private logger = new Logger(McuSender.name);

  constructor(private readonly serialport: SerialPort) {}

  send<T extends BaseDto>(data: T): Promise<void> {
    const serializer = serializers[data.dtoName];
    if (!serializer) {
      this.logger.warn('No serializer found for the given DTO');
      return;
    }
    const serializedData = serializer.serialize(data);
    this.serialport.write(serializedData);
    this.logger.info(`Send serialized data: ${serializedData}`);
  }
}
