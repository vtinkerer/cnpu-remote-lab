import { Logger } from '../../logger/logger';
import { McuDeserializer } from './mcu-deserializer';
import { IMcuReceiver, McuMessage } from './mcu.plugin';
import EventEmitter from 'events';

import { DelimiterParser } from 'serialport';

export class McuReceiver implements IMcuReceiver {
  private logger = new Logger(McuReceiver.name);
  private deserializer = new McuDeserializer();

  private events = new EventEmitter();

  constructor(private readonly parser: DelimiterParser) {
    this.parser.on('data', (buff) => {
      const data = buff.toString();
      const deserialized = this.deserializer.deserialize(data);
      if (!deserialized) {
        this.events.emit('error', new Error(`Invalid data received: ${data}`));
        return;
      }
      this.events.emit('data', deserialized);
    });

    this.parser.on('error', (error) => {
      this.events.emit('error', new Error(`Error in parser: ${error.message}`));
    });
  }

  on(event: 'data', listener: (data: McuMessage) => void): void;
  on(event: 'error', listener: (error: Error) => void): void;
  on(event: unknown, listener: unknown): void {
    this.events.on(event as string, listener as (...args: any[]) => void);
  }
}
