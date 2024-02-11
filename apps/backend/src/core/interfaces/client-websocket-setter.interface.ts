import * as WebSocket from 'ws';

export interface IClientWebsocketSetter {
  setWebsocket(websocket: WebSocket): void;
  clearWebsocket(): void;
}
