import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox';
import fastify from 'fastify';
import './fastify-typing';
import fastifyEnv from '@fastify/env';
import WebSocket from '@fastify/websocket';
import fp from 'fastify-plugin';
import { createClientWebsocketConnection } from '../client-interfaces/websocket/client-websocket-connection';
import { IMcuReceiver, mcuPlugin } from '../client-interfaces/mcu/mcu.plugin';
import { ConfigType, configSchema } from '../config/config';
import { Logger } from '../logger/logger';
import { UserRepository } from '../adapters/user.repository';
import { ClientWebsocketAdapter } from '../adapters/client-websocket.adapter';
import { ClientConnectTimeoutAdapter } from '../adapters/client-connect-timeout.adapter';
import { universalRoutes } from '../client-interfaces/http/routes/universal-route';
import { postCreateSessionRoute } from '../client-interfaces/http/routes/post-create-session';
import { getApiVersionRoute } from '../client-interfaces/http/routes/get-api-version';
import { getSessionsTest } from '../client-interfaces/http/routes/get-sessions-test';
import { getSessionStatus } from '../client-interfaces/http/routes/get-session-status';
import { postOrDeleteSessionRoutes } from '../client-interfaces/http/routes/post-or-delete-session';
import { getInitUserState } from '../client-interfaces/http/routes/get-init-user-state';
import { errorHandler } from '../client-interfaces/http/error-handler';
import {
  IScopeReader,
  scopePlugin,
} from '../client-interfaces/scope/scope.plugin';
import { IMcuSender } from '../core/interfaces/mcu-sender.interface';
import { ClientDisconnectTimeoutAdapter } from '../adapters/client-disconnect-timeout.adapter';
import { createFakeUserSessionPlugin } from '../fakes/user-session.fake';
import path from 'node:path';
import fs from 'node:fs';

export type AppDependenciesOverrides = {
  mcu?: {
    receiver: IMcuReceiver;
    sender: IMcuSender;
  };
  scope?: {
    reader: IScopeReader;
  };
};

const envFilePath = path.resolve(process.cwd(), '.env');
// console.log('envFilePath', envFilePath);
const fileContent = fs.readFileSync(envFilePath, 'utf8');
// console.log('fileContent', fileContent);

export function buildApp() {
  const server = fastify({
    logger: true,
    // disableRequestLogging: true,
  }).withTypeProvider<TypeBoxTypeProvider>();

  // Logger
  Logger.setAppLogger(server.log);

  const logger = new Logger(buildApp.name);

  // Config
  server.register(fastifyEnv, {
    confKey: 'config',
    schema: configSchema,
    dotenv: {
      path: envFilePath,
    },
    // env,
  });

  // Decorators
  server.register(
    fp(async (fastify, ops) => {
      const userRepository = new UserRepository(
        fastify.config.weblab_expired_users_timeout_seconds
      );
      fastify.decorate('userRepository', {
        getter() {
          return userRepository;
        },
      });
    })
  );
  server.register(
    fp(async (fastify, ops) => {
      const clientWebsocketAdapter = new ClientWebsocketAdapter();
      fastify.decorate('clientWebsocketAdapter', {
        getter() {
          return clientWebsocketAdapter;
        },
      });
    })
  );
  server.register(
    fp(async (fastify, ops) => {
      const clientConnectTimeoutAdapter = new ClientConnectTimeoutAdapter(
        fastify.userRepository,
        fastify.config.client_connect_timeout_seconds
      );
      fastify.decorate('clientConnectTimeoutAdapter', {
        getter() {
          return clientConnectTimeoutAdapter;
        },
      });
      fastify.addHook('onClose', (instance, done) => {
        const client = instance.clientConnectTimeoutAdapter;
        try {
          client.clearTimeoutIfExists();
        } catch (error) {}
        done();
      });
    })
  );
  server.register(
    fp(async (fastify, ops) => {
      const clientDisonnectTimeoutAdapter = new ClientDisconnectTimeoutAdapter(
        fastify.userRepository,
        fastify.config.client_disconnect_timeout_seconds
      );
      fastify.decorate('clientDisconnectTimeoutAdapter', {
        getter() {
          return clientDisonnectTimeoutAdapter;
        },
      });
      fastify.addHook('onClose', (instance, done) => {
        const client = instance.clientDisconnectTimeoutAdapter;
        try {
          client.clearTimeoutIfExists();
        } catch (error) {}
        done();
      });
    })
  );

  // Interfaces
  server.register(WebSocket);
  server.register(mcuPlugin());
  server.register(scopePlugin());

  server.register(universalRoutes);

  // Routes for LDE
  server.register(postCreateSessionRoute, { prefix: '/ldl' });
  server.register(getApiVersionRoute, { prefix: '/ldl' });
  server.register(getSessionsTest, { prefix: '/ldl' });
  server.register(getSessionStatus, { prefix: '/ldl' });
  server.register(postOrDeleteSessionRoutes, { prefix: '/ldl' });

  // ROUTES for USER
  server.register(createClientWebsocketConnection, { prefix: '/ws' });
  server.register(getInitUserState, { prefix: '/api' });

  // Errors/Exceptions
  server.setErrorHandler(errorHandler);

  server.register(createFakeUserSessionPlugin());

  return server;
}
