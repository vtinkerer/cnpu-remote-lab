import { GetUserInitStateResponse } from '@cnpu-remote-lab-nx/shared';
import { Logger } from '../../logger/logger';
import {
  AnonymousUser,
  CurrentUser,
  ExpiredUser,
} from '../entities/user.entity';
import { IUserRepository } from '../interfaces/user-repository.interface';

export class GetUserInitState {
  private logger = new Logger(GetUserInitState.name);

  constructor(private readonly userRepository: IUserRepository) {}

  async execute(sessionId: string): Promise<GetUserInitStateResponse> {
    this.logger.info('Getting user init state');

    const user = await this.userRepository.getUser(sessionId);

    this.logger.info(user);

    if (user instanceof AnonymousUser) {
      this.logger.info('Unknown user');
      return {
        isActive: false,
      };
    }

    if (user instanceof CurrentUser && !user.isActive()) {
      this.logger.info('User is current, but not active');
      return {
        isActive: false,
        url: user.back,
      };
    }

    if (user instanceof ExpiredUser) {
      this.logger.info('User is expired');
      return {
        isActive: false,
        url: user.back,
      };
    }

    this.logger.info('User is active');

    return {
      isActive: true,
      stopDate: user.maxDate.toISO(),
    };
  }
}
