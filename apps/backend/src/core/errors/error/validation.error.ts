import { AppHttpError } from '../http-error.abstract';

export class ValidationError extends AppHttpError {
  get statusCode() {
    return 422;
  }

  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}
