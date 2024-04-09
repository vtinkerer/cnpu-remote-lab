import { Static, Type } from '@sinclair/typebox';
import { WithSchemaDecorator } from '../../decorators/with-schema-validation.decorator.js';
import { DateTime } from 'luxon';
import { createLdlToken } from '../../utils/create-ldl-token.js';
import { IUserRepository } from '../interfaces/user-repository.interface.js';
import { Logger } from '../../logger/logger.js';
import { CurrentUser } from '../entities/user.entity.js';
import { IClientConnectTimeoutManager } from '../interfaces/client-connect-timeout-manager.interface.js';

export const StartSessionPayloadValidationSchema = Type.Object({
  request: Type.Object({
    locale: Type.String(),
    ldeReservationId: Type.String(),
    user: Type.Object({}),
    server: Type.Object({}),
    backUrl: Type.String(),
  }),
  laboratory: Type.Object({
    name: Type.String(),
    category: Type.Union([Type.Null(), Type.String()]),
  }),
  user: Type.Object({
    username: Type.String(),
    unique: Type.String(),
    fullName: Type.Union([Type.Null(), Type.String()]),
  }),
  schedule: Type.Object({
    start: Type.String({ format: 'date-time' }),
    length: Type.Number(),
  }),
});

export type SessionsPostBodyType = Static<
  typeof StartSessionPayloadValidationSchema
>;

export class StartSessionsUsecase {
  private logger = new Logger(StartSessionsUsecase.name);

  constructor(
    private readonly userRepository: IUserRepository,
    private readonly clientConnectTimeoutAdapter: IClientConnectTimeoutManager,
    private readonly callbackUrl: string
  ) {}

  @WithSchemaDecorator(StartSessionPayloadValidationSchema)
  async execute(payload: SessionsPostBodyType) {
    const experimentId = payload.laboratory.category
      ? `${payload.laboratory.name}@${payload.laboratory.category}`
      : payload.laboratory.name;

    const maxDate = DateTime.fromISO(payload.schedule.start).plus({
      seconds: payload.schedule.length,
    });

    const sessionId = createLdlToken();

    const user = new CurrentUser({
      username: payload.user.username,
      back: payload.request.backUrl,
      data: {},
      exited: false,
      experimentId: experimentId,
      fullName: payload.user.fullName ?? undefined,
      experimentName: payload.laboratory.name,
      categoryName: payload.laboratory.category,
      sessionId: sessionId,
      startDate: DateTime.fromISO(payload.schedule.start),
      maxDate: maxDate,
      lastPoll: DateTime.now().toUTC(),
      locale: payload.request.locale,
      requestClientData: payload.request.user,
      requestServerData: payload.request.server,
      usernameUnique: payload.user.unique,
    });

    await this.userRepository.addUser(sessionId, user);

    this.clientConnectTimeoutAdapter.startTimeout();

    this.logger.info(`Session started: ${sessionId}`);

    return {
      url: `${this.callbackUrl}?session_id=${sessionId}`,
      sessionId,
    };
  }
}
