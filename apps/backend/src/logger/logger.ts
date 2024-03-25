import pino, { BaseLogger } from 'pino';

export interface ILogger {
  info: pino.LogFn;
  error: pino.LogFn;
  warn: pino.LogFn;
}

export class Logger implements ILogger {
  static logger: BaseLogger | null = null;
  static setAppLogger(appLogger: BaseLogger) {
    Logger.logger = appLogger;
  }

  constructor(private readonly context: string) {}

  private doLog(level: 'info' | 'error' | 'warn', arg: any) {
    if (!Logger.logger) {
      throw new Error('Logger not initialized');
    }

    if (arg instanceof Error) {
      return Logger.logger[level]({
        context: this.context,
        msg: arg.message,
        stack: arg.stack,
      });
    }
    if (arg instanceof Object) {
      return Logger.logger[level]({ context: this.context, msg: arg });
    }
    if (typeof arg === 'string') {
      return Logger.logger[level]({ context: this.context, msg: arg });
    }
    return Logger.logger[level](arg);
  }

  info(arg: any) {
    this.doLog('info', arg);
  }

  error(arg: any) {
    this.doLog('error', arg);
  }

  warn(arg: any) {
    this.doLog('warn', arg);
  }
}
