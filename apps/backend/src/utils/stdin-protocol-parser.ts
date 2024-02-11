import EventEmitter from 'events';

export class StdinProtocolParser {
  private events = new EventEmitter();
  private buffer = '';

  constructor(private readonly delimiter: string) {}

  on(e: 'data', listener: (v: string) => void): void {
    this.events.on('data', listener);
  }

  process(message: string) {
    this.buffer += message;
    const splitted = this.buffer.split(this.delimiter);
    for (const partIdStr in splitted) {
      const partId = parseInt(partIdStr, 10);
      if (partId < splitted.length - 1) {
        this.events.emit('data', splitted[partId]);
      }
    }
    this.buffer = splitted[splitted.length - 1];
  }
}
