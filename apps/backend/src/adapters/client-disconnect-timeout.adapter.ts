import { IClientDisconnectTimeoutManager } from '../core/interfaces/client-disconnect-timeout-manager.interface';
import { IUserRepository } from '../core/interfaces/user-repository.interface';
import { ForceExitUserUsecase } from '../core/usecases/force-exit-user.usecase';
import { Logger } from '../logger/logger';

export class ClientDisconnectTimeoutAdapter
  implements IClientDisconnectTimeoutManager
{
  private timeout: NodeJS.Timeout | null = null;

  private logger = new Logger(ClientDisconnectTimeoutAdapter.name);

  constructor(
    private readonly userRepository: IUserRepository,
    private readonly clientDisonnectTimeoutSeconds: number
  ) {}

  startTimeout(): void {
    if (this.timeout) {
      throw new Error('Unexpected disconnect timeout call');
    }
    this.timeout = setTimeout(() => {
      const usecase = new ForceExitUserUsecase(this.userRepository);
      usecase.execute();
      this.timeout = null;
    }, this.clientDisonnectTimeoutSeconds * 1000);
  }

  clearTimeoutIfExists(): boolean {
    if (!this.timeout) {
      this.logger.warn('No disconnect timeout to clear');
      return false;
    }
    clearTimeout(this.timeout);
    this.timeout = null;
    return true;
  }
}
