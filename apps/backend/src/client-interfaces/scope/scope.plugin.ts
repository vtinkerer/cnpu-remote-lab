import fp from 'fastify-plugin';
import { Logger } from '../../logger/logger';
import { ScopeError } from '../../core/errors/scope.error';
import { SendScopeDataToUserUsecase } from '../../core/usecases/send-scope-data-to-user.usecase';
import { ScopeData } from '@cnpu-remote-lab-nx/shared';
import * as child_process from 'child_process';
import { ScopeReader } from './scope-reader';
import { createFakeScope } from '../../fakes/scope.fake';
import { IScopeSender } from '../../core/interfaces/scope-sender.interface';
import { ScopeSender } from '../../adapters/scope-sender';

export interface IScopeReader {
  on(event: 'scope-data', listener: (data: ScopeData) => void): void;
  on(event: 'error', listener: (error: string) => void): void;

  once(event: 'scope-data', listener: (data: ScopeData) => void): void;
}

export const scopePlugin = () =>
  fp(async (fastify, ops) => {
    const logger = new Logger('scopePlugin');

    let scopeReader: IScopeReader;
    let scopeSender: IScopeSender;

    if (!fastify.config.is_fake_scope) {
      const pythonProcess = child_process.spawn('python3', [
        fastify.config.scope_script_path,
      ]);
      scopeReader = new ScopeReader(
        pythonProcess,
        fastify.config.scope_script_delimiter
      );
      scopeSender = new ScopeSender(pythonProcess);
    } else {
      scopeReader = createFakeScope();
      scopeSender = null;
    }

    scopeReader.on('scope-data', async (scopeData) => {
      const usecase = new SendScopeDataToUserUsecase(
        fastify.clientWebsocketAdapter
      );
      await usecase.execute(scopeData);
    });

    const errorData = [];
    scopeReader.on('error', (data) => {
      errorData.push(data.toString());
      setTimeout(() => {
        logger.error(new ScopeError(errorData.join('*********\n')));
        process.exit(1);
      }, 2000);
    });

    fastify.decorate('scopeSender', {
      getter() {
        return scopeSender;
      },
    });

    // Pause until the python process is ready
    return new Promise((resolve, reject) => {
      scopeReader.once('scope-data', (data) => {
        resolve();
      });
    });
  });
