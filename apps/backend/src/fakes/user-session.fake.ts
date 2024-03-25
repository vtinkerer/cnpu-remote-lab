import fp from 'fastify-plugin';
import { StartSessionsUsecase } from '../core/usecases/start-session.usecase';
import { Logger } from '../logger/logger';
import { CurrentUser } from '../core/entities/user.entity';
import { DateTime } from 'luxon';

export const createFakeUserSessionPlugin = () =>
  fp(async (fastify, ops) => {
    const logger = new Logger('createFakeUserSessionPlugin');
    const fakeUser = new CurrentUser({
      back: 'http://fake-back-url:8080',
      data: {},
      exited: false,
      experimentId: 'fake-experiment-id',
      experimentName: 'fake-experiment-name',
      lastPoll: DateTime.now().toUTC(),
      maxDate: DateTime.now().plus({ year: 10 }).toUTC(),
      requestClientData: {},
      requestServerData: {},
      sessionId: fastify.config.fake_user_session_id,
      startDate: DateTime.now().minus({ second: 10 }).toUTC(),
      username: 'fake-username',
      usernameUnique: 'fake-username-unique',
      categoryName: 'fake-category-name',
      fullName: 'fake-full-name',
      locale: 'en',
    });

    await fastify.userRepository.addUser(
      fastify.config.fake_user_session_id,
      fakeUser
    );
  });
