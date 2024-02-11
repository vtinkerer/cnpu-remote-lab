import { AppHttpError } from '../http-error.abstract';

export class UnauthorizedError extends AppHttpError {
  get statusCode() {
    return 401;
  }

  constructor(message?: string) {
    super(message);
    this.name = 'UnauthorizedError';
  }
}
