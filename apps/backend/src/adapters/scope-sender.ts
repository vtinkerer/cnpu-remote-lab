import { IScopeSender } from '../core/interfaces/scope-sender.interface';
import * as child_process from 'child_process';

export class ScopeSender implements IScopeSender {
  constructor(private readonly childProcess: child_process.ChildProcess) {}

  sendOutVoltage(volts: number): void {
    this.childProcess.stdin.write(volts + '\n');
  }
}
