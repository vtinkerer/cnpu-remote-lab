import { ConfigType } from '../config/config';
import { IClientConnectTimeoutManager } from '../core/interfaces/client-connect-timeout-manager.interface';
import { IClientDataSender } from '../core/interfaces/client-data-sender.interface';
import { IClientDisconnectTimeoutManager } from '../core/interfaces/client-disconnect-timeout-manager.interface';
import { IClientWebsocketSetter } from '../core/interfaces/client-websocket-setter.interface';
import { IMcuResetter } from '../core/interfaces/mcu-resetter.interface';
import { IMcuSender } from '../core/interfaces/mcu-sender.interface';
import { IScopeSender } from '../core/interfaces/scope-sender.interface';
import { IUserRepository } from '../core/interfaces/user-repository.interface';

declare module 'fastify' {
  interface FastifyInstance {
    config: ConfigType;
    userRepository: IUserRepository;
    clientWebsocketAdapter: IClientDataSender & IClientWebsocketSetter;
    clientConnectTimeoutAdapter: IClientConnectTimeoutManager;
    clientDisconnectTimeoutAdapter: IClientDisconnectTimeoutManager;
    mcuSender: IMcuSender;
    scopeSender: IScopeSender;
    mcuResetter: IMcuResetter;
  }
}
