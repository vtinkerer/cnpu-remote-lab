import { Logger } from '../../logger/logger';
import { IUserRepository } from '../interfaces/user-repository.interface';

export class ForceExitUserUsecase {
  private logger = new Logger(ForceExitUserUsecase.name);

  constructor(private userRepository: IUserRepository) {}

  execute() {
    this.logger.info('Force exit user usecase executed');
    this.userRepository.markCurrentUserAsExited();
  }
}
