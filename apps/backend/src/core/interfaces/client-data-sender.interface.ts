import { BaseDto } from '@cnpu-remote-lab-nx/shared';

export interface IClientDataSender {
  send<T extends BaseDto>(dto: T): void;

  isAlive(): boolean;
}
