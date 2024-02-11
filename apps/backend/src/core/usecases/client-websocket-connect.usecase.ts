import * as WebSocket from 'ws';
import { IClientWebsocketSetter } from '../interfaces/client-websocket-setter.interface';
import { IClientConnectTimeoutManager } from '../interfaces/client-connect-timeout-manager.interface';
import { IClientDisconnectTimeoutManager } from '../interfaces/client-disconnect-timeout-manager.interface';
import { Logger } from '../../logger/logger';

export class ClientWebsocketConnectUsecase {
  private logger = new Logger(ClientWebsocketConnectUsecase.name);

  constructor(
    private clientWebsocketAdapter: IClientWebsocketSetter,
    private clientConnectTimeoutAdapter: IClientConnectTimeoutManager,
    private clientDisconnectAdapter: IClientDisconnectTimeoutManager
  ) {}

  execute(websocket: WebSocket): void {
    this.clientConnectTimeoutAdapter.clearTimeoutIfExists();
    const res = this.clientDisconnectAdapter.clearTimeoutIfExists();
    this.logger.info(`Client disconnect timeout cleared: ${res}`);
    this.clientWebsocketAdapter.setWebsocket(websocket);
  }
}
