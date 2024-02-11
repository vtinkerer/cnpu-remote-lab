import { Static, Type } from '@sinclair/typebox';
import { Logger } from '../../logger/logger';
import { NotFoundError } from '../errors/error/not-found.error';
import { IUserRepository } from '../interfaces/user-repository.interface';
import { WithSchemaDecorator } from '../../decorators/with-schema-validation.decorator';
import { CurrentUser } from '../entities/user.entity';
import { IClientWebsocketSetter } from '../interfaces/client-websocket-setter.interface';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import { SessionIsOver } from '@cnpu-remote-lab-nx/shared';
import { IClientConnectTimeoutManager } from '../interfaces/client-connect-timeout-manager.interface';
import { IClientDisconnectTimeoutManager } from '../interfaces/client-disconnect-timeout-manager.interface';

export const DisposeExperimentPayloadValidationSchema = Type.Object({
  sessionId: Type.String(),
  waiting: Type.Boolean(),
});

export type DisposeExperimentPostBodyType = Static<
  typeof DisposeExperimentPayloadValidationSchema
>;

export class DisposeExperimentUsecase {
  private logger = new Logger(DisposeExperimentUsecase.name);

  constructor(
    private readonly userRepository: IUserRepository,
    private readonly clientWebsocketHandler: IClientWebsocketSetter &
      IClientDataSender,
    private readonly clientConnectTimeoutAdapter: IClientConnectTimeoutManager,
    private readonly clientDisconnectTimeoutAdapter: IClientDisconnectTimeoutManager
  ) {}

  @WithSchemaDecorator(DisposeExperimentPayloadValidationSchema)
  async execute({
    sessionId,
    waiting,
  }: DisposeExperimentPostBodyType): Promise<void> {
    const user = await this.userRepository.getUser(sessionId);

    if (user.isAnonymous()) {
      throw new NotFoundError();
    }

    if (user instanceof CurrentUser) {
      const currentExpiredUser = user.toExpiredUser();
      const deleted = await this.userRepository.deleteUser(
        sessionId,
        currentExpiredUser
      );

      if (deleted) {
        // TODO: Clean resources
        this.clientWebsocketHandler.send(
          new SessionIsOver({
            backUrl: currentExpiredUser.back,
          })
          // { backUrl: currentExpiredUser.back }
        );
        this.clientWebsocketHandler.clearWebsocket();
        this.clientConnectTimeoutAdapter.clearTimeoutIfExists();
        this.clientDisconnectTimeoutAdapter.clearTimeoutIfExists();
      }
    }
  }
}
