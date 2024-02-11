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

  private doLog(level: 'info' | 'error' | 'warn', ...args: any[]) {
    const arg = args[0];

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
    // @ts-expect-error
    return Logger.logger[level](...args);
  }

  info(...args: any[]) {
    this.doLog('info', ...args);
  }

  error(...args: any[]) {
    this.doLog('error', ...args);
  }

  warn(...args: any[]) {
    this.doLog('warn', ...args);
  }
}
