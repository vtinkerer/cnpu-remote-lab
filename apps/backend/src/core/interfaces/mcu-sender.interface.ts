import { BaseDto } from '@cnpu-remote-lab-nx/shared';

export interface IMcuSender {
  send<T extends BaseDto>(data: T | T[]): Promise<void>;
}
