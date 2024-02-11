import { Logger } from '../../logger/logger';
import { CurrentUser } from '../entities/user.entity';
import { UnauthorizedError } from '../errors/error/unauthorized.error';
import { IUserRepository } from '../interfaces/user-repository.interface';

export class AuthenticateWsConnectionUsecase {
  private logger = new Logger(AuthenticateWsConnectionUsecase.name);

  constructor(private userRepository: IUserRepository) {}

  async execute(sessionId: string): Promise<void> {
    const user = await this.userRepository.getUser(sessionId);

    if (!(user instanceof CurrentUser) || !user.isActive()) {
      throw new UnauthorizedError('Not an active user');
    }

    return;
  }
}
