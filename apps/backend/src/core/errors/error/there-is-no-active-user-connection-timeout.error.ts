import { AppHttpError } from '../http-error.abstract';

export class ThereIsNoActiveUserConnectionTimeoutError extends AppHttpError {
  get statusCode() {
    return 0;
  }

  constructor(message?: string) {
    super(message);
    this.name = 'ThereIsNoActiveUserConnectionTimeout';
  }
}
