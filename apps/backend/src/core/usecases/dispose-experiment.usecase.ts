import { Static, Type } from '@sinclair/typebox';
import { Logger } from '../../logger/logger';
import { NotFoundError } from '../errors/error/not-found.error';
import { IUserRepository } from '../interfaces/user-repository.interface';
import { WithSchemaDecorator } from '../../decorators/with-schema-validation.decorator';
import { CurrentUser } from '../entities/user.entity';
import { IClientWebsocketSetter } from '../interfaces/client-websocket-setter.interface';
import { IClientDataSender } from '../interfaces/client-data-sender.interface';
import {
  CapacitorDTO,
  CurrentLoadDTO,
  LoadTypeDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  SessionIsOver,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';
import { IClientConnectTimeoutManager } from '../interfaces/client-connect-timeout-manager.interface';
import { IClientDisconnectTimeoutManager } from '../interfaces/client-disconnect-timeout-manager.interface';
import { IMcuSender } from '../interfaces/mcu-sender.interface';

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
    private readonly clientDisconnectTimeoutAdapter: IClientDisconnectTimeoutManager,
    private readonly mcuSender: IMcuSender
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
        await this.mcuSender.send(
          new PWMDTO({
            pwmPercentage: 0,
          })
        );
        await this.mcuSender.send(
          new VoltageInputDTO({
            voltage: 3,
          })
        );
        await this.mcuSender.send(
          new VoltageOutputDto({
            voltage: 0,
          })
        );
        await this.mcuSender.send(
          new CurrentLoadDTO({
            mA: 0,
          })
        );
        await this.mcuSender.send(
          new LoadTypeDTO({
            type: 'CUR',
          })
        );
        await this.mcuSender.send(
          new PWMTypeDTO({
            type: 'MAN',
          })
        );
        await this.mcuSender.send(
          new CapacitorDTO({
            capacity: 44,
          })
        );
        await this.mcuSender.send(
          new ResistanceLoadDTO({
            resistance: 9999.9,
          })
        );
      }
    }
  }
}
