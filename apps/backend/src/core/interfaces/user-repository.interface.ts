import {
  AnonymousUser,
  CurrentUser,
  ExpiredUser,
} from '../entities/user.entity';

export interface IUserRepository {
  addUser(sessionId: string, user: CurrentUser): Promise<void>;

  getUser(
    sessionId: string
  ): Promise<CurrentUser | ExpiredUser | AnonymousUser>;
  /**
   *
   * @param sessionId
   * @returns TRUE if deleted
   */
  deleteUser(sessionId: string, expiredUser: ExpiredUser): Promise<boolean>;

  updateData(sessionId: string, data: unknown): Promise<void>;

  sessionExists(sessionId: string): Promise<boolean>;

  markCurrentUserAsExited(): Promise<void>;
}
