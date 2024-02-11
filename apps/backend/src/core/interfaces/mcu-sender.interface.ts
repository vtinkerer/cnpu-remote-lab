import { ClientToServerDTO } from '@cnpu-remote-lab-nx/shared';

export interface IMcuSender {
  send<T extends ClientToServerDTO>(data: T): Promise<void>;
}
