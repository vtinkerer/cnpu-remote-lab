import EventEmitter from 'node:events';
import { StdinProtocolParser } from '../../utils/stdin-protocol-parser';
import { ScopeData } from '@cnpu-remote-lab-nx/shared';
import { IScopeReader } from './scope.plugin';
import * as child_process from 'child_process';

export class ScopeReader implements IScopeReader {
  private readonly eventEmitter = new EventEmitter();
  private readonly inputParser: StdinProtocolParser;

  constructor(
    private readonly pythonProcess: child_process.ChildProcess,
    private readonly delimiter: string
  ) {
    this.inputParser = new StdinProtocolParser(this.delimiter);

    this.inputParser.on('data', async (data) => {
      let scopeData: ScopeData;
      try {
        scopeData = JSON.parse(data);
      } catch (error) {
        this.eventEmitter.emit('error', error.toString());
        return;
      }

      if (
        scopeData[0].hasOwnProperty('t') &&
        scopeData[0].hasOwnProperty('v')
      ) {
        this.eventEmitter.emit('scope-data', scopeData);
        return;
      }

      this.eventEmitter.emit('error', 'Unknown scope data');
    });

    this.pythonProcess.stdout.on('data', (data) => {
      this.inputParser.process(data.toString());
    });

    this.pythonProcess.stderr.on('data', (data) => {
      this.eventEmitter.emit('error', data.toString());
    });

    this.pythonProcess;
  }

  on(event: 'scope-data', listener: (data: ScopeData) => void): void;
  on(event: 'error', listener: (error: string) => void): void;
  on(event: unknown, listener: unknown): void {
    if (event === 'scope-data') {
      this.eventEmitter.on('scope-data', listener as (data: ScopeData) => void);
    } else if (event === 'error') {
      this.eventEmitter.on('error', listener as (error: Error) => void);
    }
  }

  once(event: 'scope-data', listener: (data: ScopeData) => void): void {
    this.eventEmitter.once('scope-data', listener);
  }
}
