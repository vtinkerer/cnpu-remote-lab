import { AppError } from './app-error.abstract';

export class ScopeError extends AppError {
  constructor(message?: string) {
    super(message);
    this.name = ScopeError.name;
  }
}
