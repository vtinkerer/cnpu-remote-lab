import * as WebSocket from 'ws';
import { IClientDataSender } from '../core/interfaces/client-data-sender.interface';
import { IClientWebsocketSetter } from '../core/interfaces/client-websocket-setter.interface';
import { BaseDto } from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../logger/logger';

export class ClientWebsocketAdapter
  implements IClientDataSender, IClientWebsocketSetter
{
  private logger = new Logger(ClientWebsocketAdapter.name);

  private websocket: WebSocket | null = null;

  setWebsocket(websocket: WebSocket): void {
    this.websocket = websocket;
  }

  clearWebsocket(): void {
    this.logger.info('Clearing websocket');
    this.websocket?.terminate();
    this.websocket = null;
  }

  send<T extends BaseDto>(dto: T): void {
    if (!this.websocket) {
      this.logger.warn('Trying to send data to a non-existing websocket');
      return;
    }
    this.websocket.send(JSON.stringify(dto));
  }

  isAlive(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }
}
