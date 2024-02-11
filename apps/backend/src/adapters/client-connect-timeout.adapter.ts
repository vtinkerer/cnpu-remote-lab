import { ThereIsNoActiveUserConnectionTimeoutError } from '../core/errors/error/there-is-no-active-user-connection-timeout.error';
import { IClientConnectTimeoutManager } from '../core/interfaces/client-connect-timeout-manager.interface';
import { IUserRepository } from '../core/interfaces/user-repository.interface';
import { ForceExitUserUsecase } from '../core/usecases/force-exit-user.usecase';
import { Logger } from '../logger/logger';

export class ClientConnectTimeoutAdapter
  implements IClientConnectTimeoutManager
{
  private timeout: NodeJS.Timeout | null = null;

  private logger = new Logger(ClientConnectTimeoutAdapter.name);

  constructor(
    private readonly userRepository: IUserRepository,
    private readonly clientConnectTimeoutSeconds: number
  ) {}

  startTimeout(): void {
    if (this.timeout) throw new ThereIsNoActiveUserConnectionTimeoutError();
    this.timeout = setTimeout(() => {
      this.logger.info('Client connect timeout fired');
      const usecase = new ForceExitUserUsecase(this.userRepository);
      usecase.execute();
      this.timeout = null;
    }, this.clientConnectTimeoutSeconds * 1000);
  }

  clearTimeoutIfExists(): boolean {
    if (!this.timeout) {
      this.logger.warn('No connect timeout to clear');
      return false;
    }
    clearTimeout(this.timeout);
    this.timeout = null;
    return true;
  }
}
