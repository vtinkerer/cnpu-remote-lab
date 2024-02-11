import { IUserRepository } from '../interfaces/user-repository.interface';
import { Logger } from '../../logger/logger';
import { CurrentUser, ExpiredUser } from '../entities/user.entity';

export class GetSessionStatusUsecase {
  private readonly logger = new Logger(GetSessionStatusUsecase.name);

  constructor(
    private readonly userRepository: IUserRepository,
    private readonly pollInterval: number,
    private readonly weblabTimeout: number
  ) {}

  async execute(sessionId: string) {
    const user = await this.userRepository.getUser(sessionId);

    if (user instanceof ExpiredUser && user.isDisposingResources) {
      return 2;
    }

    if (user.isAnonymous() || !(user instanceof CurrentUser)) {
      return -1;
    }

    if (user.exited) {
      return -1;
    }

    if (
      this.weblabTimeout > 0 &&
      user.timeWithoutPolling() >= this.weblabTimeout
    ) {
      return -1;
    }

    if (user.timeLeft() <= 0) {
      return -1;
    }

    return Math.min(this.pollInterval, Math.floor(user.timeLeft()));
  }
}
