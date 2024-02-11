import { randomBytes } from 'crypto';

export function createLdlToken(size = 32) {
  return randomBytes(size).toString('hex');
}
