import { IClientDisconnectTimeoutManager } from '../interfaces/client-disconnect-timeout-manager.interface';
import { IClientWebsocketSetter } from '../interfaces/client-websocket-setter.interface';

export class ClientWebsocketDisconnectUsecase {
  constructor(
    private clientWebsocketAdapter: IClientWebsocketSetter,
    private clientDisconnectAdapter: IClientDisconnectTimeoutManager
  ) {}

  execute(): void {
    this.clientWebsocketAdapter.clearWebsocket();
    this.clientDisconnectAdapter.startTimeout();
  }
}
