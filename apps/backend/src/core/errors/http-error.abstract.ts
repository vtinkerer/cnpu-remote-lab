import { AppError } from './app-error.abstract';

export abstract class AppHttpError extends AppError {
  abstract statusCode: number;
}
