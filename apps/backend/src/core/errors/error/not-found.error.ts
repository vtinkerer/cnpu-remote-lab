import { AppHttpError } from '../http-error.abstract';

// Please note that according to Fastify docs, it's handled separately from other errors.
export class NotFoundError extends AppHttpError {
  get statusCode() {
    return 404;
  }

  constructor(message?: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}
