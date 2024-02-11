import { DateTime } from 'luxon';
import { IUserRepository } from '../core/interfaces/user-repository.interface';
import { Logger } from '../logger/logger';
import {
  AnonymousUser,
  CurrentUser,
  ExpiredUser,
} from '../core/entities/user.entity';

export class UserRepository implements IUserRepository {
  private logger = new Logger(UserRepository.name);

  private currentUser: CurrentUser | null = null;

  private expiredUsers: ExpiredUser[] = [];

  private expirationTimeouts: { sessionId: string; timeout: NodeJS.Timeout }[] =
    [];

  constructor(private readonly expiredUsersTimeoutSeconds: number) {}

  async addUser(sessionId: string, user: CurrentUser): Promise<void> {
    this.currentUser = user;
  }

  async getUser(
    sessionId: string
  ): Promise<CurrentUser | ExpiredUser | AnonymousUser> {
    if (this.currentUser?.sessionId === sessionId) {
      return this.currentUser;
    }

    const expiredUser = this.expiredUsers.find(
      (u) => u.sessionId === sessionId
    );
    if (expiredUser) {
      return expiredUser;
    }

    return new AnonymousUser();
  }

  async deleteUser(
    sessionId: string,
    expiredUser: ExpiredUser
  ): Promise<boolean> {
    if (!this.currentUser) {
      return false;
    }
    this.currentUser = null;
    this.expiredUsers.push(expiredUser);

    const timeout = setTimeout(() => {
      const userIndex = this.expiredUsers.findIndex(
        (u) => u.sessionId === sessionId
      );
      if (userIndex !== -1) {
        this.expiredUsers.splice(userIndex, 1);
      }
      const timeoutIndex = this.expirationTimeouts.findIndex(
        (t) => t.sessionId === sessionId
      );
      if (timeoutIndex !== -1) {
        this.expirationTimeouts.splice(timeoutIndex, 1);
      }
    }, this.expiredUsersTimeoutSeconds * 1000);
    this.expirationTimeouts.push({ sessionId, timeout });

    return true;
  }

  async updateData(sessionId: string, data: unknown): Promise<void> {
    let user: CurrentUser | ExpiredUser | null;

    if (this.currentUser?.sessionId === sessionId) {
      user = this.currentUser;
    } else {
      user = this.expiredUsers.find((u) => u.sessionId === sessionId) ?? null;
    }

    if (!user) {
      throw new Error('You tried to update data of a non-existing user');
    }

    user.data = data;
  }

  async sessionExists(sessionId: string): Promise<boolean> {
    return (
      this.currentUser?.sessionId === sessionId ||
      this.expiredUsers.some((u) => u.sessionId === sessionId)
    );
  }

  async markCurrentUserAsExited(): Promise<void> {
    if (!this.currentUser) {
      this.logger.warn('No current user to mark as exited');
      return;
    }
    this.currentUser.exited = true;
  }
}
